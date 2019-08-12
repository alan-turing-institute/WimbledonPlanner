import pandas as pd
import holidays
from copy import deepcopy
import sqlalchemy as sqla
import os.path
import subprocess
import re
import numpy as np

import wimbledon.config
import wimbledon.harvest.api_interface
from wimbledon.sql import update_db
from wimbledon.sql import query_db


def get_business_days(start_date, end_date):
    """Get a daily time series between start_date and end_date
    excluding weekends and public holidays."""

    date_range = pd.date_range(start=start_date,
                               end=end_date,
                               freq=pd.tseries.offsets.BDay())

    # remove public holidays
    pub_hols = holidays.England()
    date_range = pd.to_datetime([date for date in date_range
                                 if date not in pub_hols])

    return date_range


def select_date_range(df, start_date, end_date, drop_zero_cols=True):
    """Extract a range of dates from a dataframe with a datetime index,
    then remove any columns which are left empty (full of zeros)."""
    mask = (df.index >= start_date) & (df.index <= end_date)
    df_slice = df.loc[mask]

    if drop_zero_cols:
        nonzero_cols = df_slice.columns[df_slice.sum() != 0]
        df_slice = df_slice[nonzero_cols]

    return df_slice


class Wimbledon:
    """Load and group Forecast data"""
    def __init__(self,
                 update_db=False,
                 work_hrs_per_day=None,
                 proj_hrs_per_day=None):

        if update_db:
            update_db()

        data = query_db.get_data()
        self.people = data['people']
        self.projects = data['projects']
        self.assignments = data['assignments']
        self.clients = data['clients']
        self.tasks = data['tasks']
        self.time_entries = data['time_entries']
        self.associations = data['associations']

        # Find the earliest and latest date in the data, create a range
        # of weekdays between these dates
        self.date_range = get_business_days(
                            self.assignments['start_date'].min(),
                            self.assignments['end_date'].max()
                          )

        # 1 FTE hours per day
        if work_hrs_per_day is None:
            self.work_hrs_per_day = 8
        else:
            self.work_hrs_per_day = work_hrs_per_day
        
        # hours per day nominally for projects
        if proj_hrs_per_day is None:
            self.proj_hrs_per_day = 6.4
        else:
            self.proj_hrs_per_day = proj_hrs_per_day

        # Convert allocations to FTE equivalents, construct some columns from tags etc
        self.process_data()

        # people_allocations: dict with key person_id, contains df of (date, project_id) with allocation
        # people_totals: df of (date, person_id) with total allocations
        self.people_allocations, self.people_totals = self.get_allocations('person')

        # project_allocations: dict with key project_id, contains df of (date, person_id) with allocation
        # project_confirmed: df of (date, project_id) with total allocations across PEOPLE ONLY
        self.project_allocations, self.project_confirmed = self.get_allocations('project')

        # placeholder_allocations: dict with key placeholder_id, contains df of (date, project_id) with allocation
        # placeholder_totals: df of (date, placeholder_id) with total allocation
        self.placeholder_allocations, self.placeholder_totals = self.get_allocations('placeholder')

        # project_unconfirmed: df of (date, project_id) with total allocation to unconfirmed placeholders
        self.project_unconfirmed = self.get_project_unconfirmed()

        # project_deferred:  df of (date, project_id) with total allocation to deferred placeholders
        self.project_deferred = self.get_project_deferred()

        # project_confirmed: total people + institute + resource_required placeholder allocations to project
        # project_resourcereq: resource_required allocations to each project
        self.project_confirmed, self.project_resourcereq = self.get_project_required()

        self.project_allocated = self.project_confirmed - self.project_resourcereq

        # consolidated allocations for resource required, unconfirmed, deferred (may be split over multiple placeholders
        # on Forecast)
        resreq_idx = [idx for idx in self.placeholders.index
                      if 'resource required' in self.placeholders.loc[idx, 'name'].lower()]

        self.resourcereq_allocations = self.placeholder_allocations[resreq_idx[0]]
        if len(resreq_idx) > 1:
            for idx in resreq_idx[1:]:
                self.resourcereq_allocations = self.resourcereq_allocations.add(self.placeholder_allocations[idx],
                                                                                fill_value=0)

        unconf_idx = [idx for idx in self.placeholders.index
                      if 'unconfirmed' in self.placeholders.loc[idx, 'name'].lower()]

        self.unconfirmed_allocations = self.placeholder_allocations[unconf_idx[0]]
        if len(unconf_idx) > 1:
            for idx in unconf_idx[1:]:
                self.unconfirmed_allocations = self.unconfirmed_allocations.add(self.placeholder_allocations[idx],
                                                                                fill_value=0)

        defer_idx = [idx for idx in self.placeholders.index
                     if 'deferred' in self.placeholders.loc[idx, 'name'].lower()]

        self.deferred_allocations = self.placeholder_allocations[defer_idx[0]]
        if len(defer_idx) > 1:
            for idx in defer_idx[1:]:
                self.deferred_allocations = self.deferred_allocations.add(self.placeholder_allocations[idx],
                                                                          fill_value=0)

        # calculate team capacity: capacity in people table minus any allocations to unavailable project
        unavailable_id = self.get_id('UNAVAILABLE', 'project')

        base_capacity = self.people.weekly_capacity

        self.capacity = pd.DataFrame(index=self.date_range, columns=self.people.index)

        for person_id in self.people.index:
            self.capacity[person_id] = base_capacity[person_id]

            if unavailable_id in self.people_allocations[person_id].columns:
                self.capacity[person_id] = self.capacity[person_id] - self.people_allocations[person_id][unavailable_id]

    def load_csv_data(self, data_dir):
        """load data from csv files in ../data/forecast directory"""

        people = pd.read_csv(data_dir+'/people.csv',
                             index_col='id',
                             parse_dates=['updated_at'],
                             infer_datetime_format=True)

        projects = pd.read_csv(data_dir+'/projects.csv',
                               index_col='id',
                               parse_dates=['updated_at', 'start_date', 'end_date'],
                               infer_datetime_format=True)

        placeholders = pd.read_csv(data_dir+'/placeholders.csv',
                                   index_col='id',
                                   parse_dates=['updated_at'],
                                   infer_datetime_format=True)

        assignments = pd.read_csv(data_dir+'/assignments.csv',
                                  index_col='id',
                                  parse_dates=['start_date', 'end_date', 'updated_at'],
                                  infer_datetime_format=True)

        clients = pd.read_csv(data_dir+'/clients.csv',
                              index_col='id',
                              parse_dates=['updated_at'],
                              infer_datetime_format=True)

        return people, projects, placeholders, assignments, clients

    def process_data(self):
        # assign missing capacities as 1 FTE, given by self.work_hrs_per_day, 5 days per week
        self.people['weekly_capacity'].fillna(self.work_hrs_per_day * 5 * 60 * 60, inplace=True)

        # convert capacity into FTE at self.work_hrs_per_day hours per day
        self.people['weekly_capacity'] = self.people['weekly_capacity'] / (self.work_hrs_per_day * 5 * 60 * 60)

        # remove project managers
        self.people = self.people[self.people.roles != "['Research Project Manager']"]

        # convert assignments in seconds per day to fractions of 1 FTE (defined by self.work_hrs_per_day)
        self.assignments['allocation'] = self.assignments['allocation'] / (self.work_hrs_per_day * 60 * 60)

    def get_person_name(self, person_id):
        """Get the name of someone from their person_id"""
        return self.people.loc[person_id, 'name']

    def get_person_id(self, name):
        """Get the person_id of someone from their first_name and last_name."""
        person_id = self.people.loc[(self.people['name'] == name)]

        if len(person_id) != 1:
            raise ValueError('Could not unique person with name ' + name)

        return person_id.index[0]

    def get_project_name(self, project_id):
        """Get the name of a project from its project_id"""
        return self.projects.loc[project_id, 'name']

    def get_project_id(self, project_name):
        """Get the id of a project from its name"""
        return self.projects.index[self.projects.name == project_name][0]

    def get_client_id(self, client_name):
        return self.clients.index[self.clients.name == client_name][0]

    def get_name(self, id_value, id_type):
        """Get the name of an id based on the type of id it is. id_type can be
        'person', 'project' or 'placeholder'"""
        if id_type == 'person':
            try:
                return self.get_person_name(id_value)
            except KeyError:
                # if person id search fails check whether it's a placeholder id
                # to deal with cases where they've been merged together
                return self.get_name(id_value, 'placeholder')

        elif id_type == 'project':
            return self.get_project_name(id_value)

        else:
            raise ValueError('id_type must be person or project')

    def get_id(self, name, id_type):
        """Get the name of an id based on the type of id it is. id_type can be
        'person', 'project' or 'placeholder'"""
        if id_type == 'person':
            try:
                return self.get_person_id(name)
            except (KeyError, ValueError):
                # if person id search fails check whether it's a placeholder id
                # to deal with cases where they've been merged together
                return self.get_placeholder_id(name)

        elif id_type == 'project':
            return self.get_project_id(name)

        else:
            raise ValueError('id_type must be person or project')

    def get_allocations(self, id_column):
        """For each unique value in id_column, create a dataframe where the rows are dates,
        the columns are projects/people/placeholders depending on id_column, and the values are
        time allocations for that date. id_column can be 'person', 'project', or 'placeholder'."""
        if id_column == 'person':
            grouped_allocations = self.assignments.groupby(
                ['person_id', 'project_id', 'start_date', 'end_date']).allocation.sum()
            id_values = self.people.index
            ref_column = 'project_id'

        elif id_column == 'project':
            grouped_allocations = self.assignments.groupby(
                ['project_id', 'person_id', 'start_date', 'end_date']).allocation.sum()
            id_values = self.projects.index
            ref_column = 'person_id'

        else:
            raise ValueError('id_column must be person or project')

        allocations = {}

        for idx in id_values:
            # check whether the this id has any assignments, i.e. whether the id
            # exists in the index (get_level_values to deal with MultiIndex)
            if idx in grouped_allocations.index.get_level_values(0):
                # get the allocations
                id_allocs = grouped_allocations.loc[idx]

                # unstack the MultiIndex
                id_allocs = id_allocs.reset_index()

                # Initialise dataframe to store results
                id_alloc_days = pd.DataFrame(index=self.date_range, columns=id_allocs[ref_column].unique())
                id_alloc_days.fillna(0, inplace=True)

                # Loop over each assignment
                for _, row in id_allocs.iterrows():
                    # Create the range of business days that this assignment corresponds to
                    dates = get_business_days(row['start_date'], row['end_date'])

                    # Add the allocation to the corresponding project for the range of dates.
                    id_alloc_days.loc[dates, row[ref_column]] += row['allocation']

            else:
                # no projects, just make an empty dataframe
                id_alloc_days = pd.DataFrame(index=self.date_range)

            # Add the person's name as a label - just nice for printing later.
            id_alloc_days.columns.name = self.get_name(idx, id_column)

            allocations[idx] = id_alloc_days

        # total assignment each day
        totals = pd.DataFrame(index=self.date_range, columns=id_values)
        for idx in allocations.keys():
            totals[idx] = allocations[idx].sum(axis=1)

        return allocations, totals

    def get_project_unconfirmed(self):
        """Get unconfirmed project requirements"""

        project_unconf_ids = self.placeholders[self.placeholders.name.str.lower().str.contains('unconfirmed')].index

        project_unconfirmed = pd.DataFrame(index=self.date_range, columns=self.projects.index)
        project_unconfirmed[:] = 0

        for idx in project_unconf_ids:
            allocs = self.placeholder_allocations[idx]

            for project in allocs.columns:
                project_unconfirmed[project] += allocs[project]

        return project_unconfirmed

    def get_project_deferred(self):
        """Get deferred project allocations"""

        project_defer_ids = self.placeholders[self.placeholders.name.str.lower().str.contains('deferred')].index

        project_deferred = pd.DataFrame(index=self.date_range, columns=self.projects.index)
        project_deferred[:] = 0

        for idx in project_defer_ids:
            allocs = self.placeholder_allocations[idx]

            for project in allocs.columns:
                project_deferred[project] += allocs[project]

        return project_deferred

    def get_project_required(self):
        """Get amount of additional resource that needs to be required over time, i.e. difference between
        project requirements and project allocations."""
        # Project requirements = Project assignments + Resource required assignments
        project_confirmed = self.project_confirmed.copy(deep=True)

        project_resourcereq = pd.DataFrame(index=self.date_range, columns=self.projects.index)
        project_resourcereq[:] = 0

        # add resource req info from placeholders
        resource_req_ids = []
        for idx in self.placeholders.index:
            name = self.placeholders.loc[idx, 'name'].lower()

            if 'resource required' in name:
                resource_req_ids.append(idx)

        for idx in resource_req_ids:
            allocs = self.placeholder_allocations[idx]

            for project in allocs.columns:
                project_confirmed[project] += allocs[project]

                if 'resource required' in self.placeholders.loc[idx, 'name'].lower():
                    project_resourcereq[project] += allocs[project]

        return project_confirmed, project_resourcereq

    def whiteboard(self, key_type, start_date, end_date, freq, add_placeholders=True):
        """Create the raw, unstyled, whiteboard visualisation.

         Dataframe with the rows being key_type (project or person ids), the columns
        dates and the cell values being either a person or project and their time allocation, sorted by time allocation.

        If add_placeholders=True, non-resource required placeholders will be included on the sheet."""

        if key_type == 'project':
            # copy to prevent overwriting original
            data_dict = deepcopy(self.project_allocations)

            mask = (self.project_resourcereq.index >= start_date) & (self.project_resourcereq.index <= end_date)
            resreq = self.project_resourcereq.loc[mask]
            unconfirmed = self.project_unconfirmed.loc[mask]
            deferred = self.project_deferred.loc[mask]

            if add_placeholders:
                # add placeholders to data_dict, excluding resource required placeholders
                placeholder_ids = []
                for idx in self.placeholders.index:
                    name = self.placeholders.loc[idx, 'name'].lower()
                    if 'resource required' in name:
                        continue
                    elif 'unconfirmed' in name:
                        continue
                    elif 'deferred' in name:
                        continue
                    else:
                        placeholder_ids.append(idx)

                for placeholder_id in placeholder_ids:
                    for project_id in self.placeholder_allocations[placeholder_id].columns:
                        data_dict[project_id].loc[:, placeholder_id] = self.placeholder_allocations[placeholder_id][project_id].copy()

        elif key_type == 'person':
            data_dict = deepcopy(self.people_allocations)

            if add_placeholders:
                # add institute/misc placeholders to data_dict (not resource required, unavailable or deferred)
                placeholder_ids = [idx for idx in self.placeholders.index
                                   if 'resource required' not in self.placeholders.loc[idx, 'name'].lower() and
                                      'unconfirmed' not in self.placeholders.loc[idx, 'name'].lower() and
                                      'deferred' not in self.placeholders.loc[idx, 'name'].lower()]

                for idx in placeholder_ids:
                    # copy needed to prevent overwriting original placeholder_allocations df later
                    data_dict[idx] = self.placeholder_allocations[idx].copy()

                data_dict['Resource Required'] = self.resourcereq_allocations.copy()
                data_dict['Unconfirmed'] = self.unconfirmed_allocations.copy()
                data_dict['Deferred'] = self.deferred_allocations.copy()

        else:
            return ValueError('key type must be person or project')

        sheet = {}

        # set of unique project names used for cell colouring later
        names = set()

        # for each project
        for key in data_dict.keys():
            # get the projects's person allocations
            df = data_dict[key]

            # replace ids with names. for project id: include resource required.
            if key_type == 'project':
                if self.get_name(key, 'project') == 'UNAVAILABLE':
                    # don't display allocations to unavailable project
                    continue

                df.columns = [self.get_name(person_id, 'person') for person_id in df.columns]
                df.columns.name = self.get_name(key, 'project')

                df['RESOURCE REQUIRED'] = resreq[key].copy()
                df['UNCONFIRMED'] = unconfirmed[key].copy()
                df['DEFERRED'] = deferred[key].copy()

            elif key_type == 'person':
                df.columns = [self.get_name(project_id, 'project') for project_id in df.columns]

                if (key == 'Resource Required') or (key == 'Unconfirmed') or (key == 'Deferred'):
                    df.columns.name = key
                else:
                    df.columns.name = self.get_name(key, 'person')

            else:
                return ValueError('key type must be person or project')

            # extract the date range of interest
            df = select_date_range(df, start_date, end_date)

            if key_type == 'person':
                if 'UNAVAILABLE' in df.columns and len(df.columns) == 1:
                    # don't display people who are only assigned as unavailable
                    continue

            # check there are project allocations to display
            if df.shape[0] > 0 and df.shape[1] > 0:

                # update the set of names
                [names.add(col) for col in df.columns]

                # resample the data to the given date frequency
                if freq != 'D':
                    df = df.resample(freq).mean()

                # sort people (column order) by magnitude of earliest assignment
                df = df.sort_values(by=[idx for idx in df.index], axis=1, ascending=False)

                # max number items assigned to this key at a time
                n_columns = (df > 0).sum(axis=1).max()

                # initialise data frame to store projects/people ranked by time assignment
                key_sheet = pd.DataFrame(index=df.index, columns=range(1, n_columns + 1))
                # empty strings for blank cells
                key_sheet[:] = ''

                fill_idx = None

                for name_idx, name in enumerate(df.columns):
                    # flags dates where this name has a non-zero allocation
                    nonzero_allocs = df.iloc[:, name_idx] > 0

                    # choose where to place new allocations in key_sheet
                    for key_col in key_sheet.columns:
                        # flags columns in key_sheet where the new allocations in df[name] overlap
                        # with previous allocations added to key_sheet
                        conflicts = key_sheet.loc[nonzero_allocs, key_col].str.len() > 0

                        # if there is no overlap between new allocations and this column we can fill the values there
                        if (~conflicts).all():
                            fill_idx = key_col
                            break

                    if fill_idx is None:
                        raise KeyError("no suitable column to fill without conflicts")

                    # insert the new allocations with format <NAME> (<ALLOCATION>)
                    key_sheet.loc[nonzero_allocs, fill_idx] = name + df.iloc[nonzero_allocs.values, name_idx].apply(lambda x: '<br>({:.1f})'.format(x))

                # remove unused columns
                [key_sheet.drop(col, axis=1, inplace=True) for col in key_sheet.columns if
                 key_sheet[col].str.len().sum() == 0]

                # format dates nicely
                if freq == 'MS':
                    key_sheet = pd.DataFrame(key_sheet, index=key_sheet.index.strftime("%b-%Y"))
                elif freq == 'W-MON':
                    key_sheet = pd.DataFrame(key_sheet, index=key_sheet.index.strftime("%d-%b-%Y"))
                else:
                    key_sheet = pd.DataFrame(key_sheet, index=key_sheet.index.strftime("%Y-%m-%d"))

                # store the allocations - transpose to get rows as keys and columns as dates
                sheet[df.columns.name] = key_sheet.T

        # merge everything together into one large dataframe, sorted by key
        sheet = pd.concat(sheet).sort_index()

        if key_type == 'project':

            # Get project client names
            proj_idx = [self.get_project_id(name) for name in sheet.index.get_level_values(0)]
            client_idx = self.projects.loc[proj_idx, 'client_id']
            client_name = self.clients.loc[client_idx, 'name']

            # Add project client info to index (~programme area)
            sheet['client_name'] = client_name.values
            sheet.set_index(['client_name', sheet.index], inplace=True)
            sheet.index.rename('project_name', 1, inplace=True)
            sheet.index.rename('row', 2, inplace=True)

            sheet.sort_values(by=['client_name', 'project_name', 'row'], inplace=True)
            
            # Move REG projects to end
            clients = client_name.unique()
            reg = sorted([client for client in clients if 'REG' in client])
            others = sorted([client for client in clients if 'REG' not in client])
            sheet = sheet.reindex(others+reg, level=0)

            # Remove index headings
            sheet.index.rename([None, None, None], inplace=True)

            # Get GitHub issue numbers, add as hrefs
            proj_names = sheet.index.levels[1].values
            proj_idx = [self.get_project_id(name) for name in proj_names]
            proj_gitissue = [self.projects.loc[idx, 'GitHub'] for idx in proj_idx]
            git_base_url = 'https://github.com/alan-turing-institute/Hut23/issues'

            proj_names_with_url = {}
            for idx, proj in enumerate(proj_names):
                if not (type(proj_gitissue[idx]) is float and np.isnan(proj_gitissue[idx])):
                    proj_names_with_url[proj] = """<a href="{url}/{issue}">{proj}</a>""".format(url=git_base_url,
                                                                                               issue=proj_gitissue[idx],
                                                                                               proj=proj)

            sheet.rename(proj_names_with_url, axis='index', level=1, inplace=True)

        elif key_type == 'person':

            # Get person association group
            person_idx = []
            for name in sheet.index.get_level_values(0):
                try:
                    person_idx.append(self.get_id(name, 'person'))
                except (KeyError, ValueError, IndexError):
                    person_idx.append('Placeholder')

            group_name = []
            for idx in person_idx:
                if idx == 'Placeholder':
                    group_name.append('Placeholder')
                else:
                    try:
                        group_name.append(self.people.loc[idx, 'association_group'])
                    except KeyError:
                        group_name.append(self.placeholders.loc[idx, 'association_group'])

            # Add project client info to index (~programme area)
            sheet['group_name'] = group_name
            sheet.set_index(['group_name', sheet.index], inplace=True)
            sheet.index.rename('person_name', 1, inplace=True)
            sheet.index.rename('row', 2, inplace=True)

            sheet.sort_values(by=['group_name', 'person_name', 'row'], inplace=True)

            sheet = sheet.reindex(['REG Director', 'REG Principal', 'REG Senior', 'REG Permanent',
                                   'REG FTC', 'REG Associate', 'University Partner', 'Placeholder'],
                                  level=0)

            sheet.index.rename([None, None, None], inplace=True)

        return sheet


class Harvest:
    """Load and group Harvest data"""

    def __init__(self, data_source='api', data_dir='', proj_hrs_per_day=None):
        self.data_source = data_source

        if data_source == 'api':
            data = wimbledon.harvest.api_interface.get_harvest()

            self.time_entries = data['time_entries']
            self.projects = data['projects']
            self.tasks = data['tasks']
            self.clients = data['clients']
            self.people = data['users']

        elif data_source == 'csv':
            self.time_entries, self.projects, self.tasks, self.clients, self.people = self.load_csv_data(data_dir)

        elif data_source == 'sql':
            self.time_entries, self.projects, self.tasks, self.clients, self.people = self.load_sql_data()

        else:
            raise ValueError('data_source must be csv or sql')

        # Find the earliest and latest date in the data, create a range of weekdays between these dates
        # NB: Harvest data needs to include non-working days as there may be time entries on these days, e.g.
        # leave or block entering data for a month on the 1st of that month.
        self.date_range = pd.date_range(start=self.time_entries['spent_date'].min(),
                                        end=self.time_entries['spent_date'].max(),
                                        freq='D')

        if proj_hrs_per_day is None:
            self.proj_hrs_per_day = 6.4
        else:
            self.proj_hrs_per_day = proj_hrs_per_day

        # remove empty columns, reformat some column names
        self.process_data()

        self.projects_tasks = self.get_entries('project', 'task')
        self.projects_people = self.get_entries('project', 'person')
        self.people_projects = self.get_entries('person', 'project')
        self.people_tasks = self.get_entries('person', 'task')
        self.people_clients = self.get_entries('person', 'client')

        # TODO exclude leave, TOIL, illness etc. from totals?
        self.projects_totals = self.get_entries('project', 'TOTAL')
        self.people_totals = self.get_entries('person', 'TOTAL')
        self.clients_totals = self.get_entries('client', 'TOTAL')
        self.tasks_totals = self.get_entries('task', 'TOTAL')

    def load_csv_data(self, data_dir):
        time_entries = pd.read_csv(data_dir+'/time_entries.csv',
                                   index_col='id',
                                   parse_dates=['created_at', 'spent_date', 'updated_at',
                                                'task_assignment.created_at', 'task_assignment.updated_at',
                                                'user_assignment.created_at', 'user_assignment.updated_at'],
                                   infer_datetime_format=True)

        projects = pd.read_csv(data_dir+'/projects.csv',
                               index_col='id',
                               parse_dates=['created_at', 'starts_on', 'ends_on', 'updated_at'],
                               infer_datetime_format=True)

        tasks = pd.read_csv(data_dir+'/tasks.csv',
                            index_col='id',
                            parse_dates=['created_at', 'updated_at'],
                            infer_datetime_format=True)

        clients = pd.read_csv(data_dir+'/clients.csv',
                              index_col='id',
                              parse_dates=['created_at', 'updated_at'],
                              infer_datetime_format=True)

        people = pd.read_csv(data_dir+'/users.csv',
                             index_col='id',
                             parse_dates=['created_at', 'updated_at'],
                             infer_datetime_format=True)

        return time_entries, projects, tasks, clients, people

    def load_sql_data(self):
        """load data from sql database defined by ../sql/config.json, which must be a json containing
        host: the server name (url)
        database: the name of the database on the server
        drivername: the type of database it is, e.g. postgresql"""

        config = wimbledon.config.get_sql_config()

        if config['host'] == 'localhost':
            url = sqla.engine.url.URL(drivername=config['drivername'],
                                      host=config['host'],
                                      database=config['database'])

            subprocess.call(['sh', '../sql/start_localhost.sh'], cwd='../sql')

        else:
            url = sqla.engine.url.URL(drivername=config['drivername'],
                                      username=config['username'],
                                      password=config['password'],
                                      host=config['host'],
                                      database=config['database'])

        engine = sqla.create_engine(url)

        connection = engine.connect()

        projects = pd.read_sql_table('projects', connection, schema='harvest',
                                     index_col='id',
                                     parse_dates=['starts_on', 'ends_on'])

        tasks = pd.read_sql_table('tasks', connection, schema='harvest',
                                  index_col='id')

        clients = pd.read_sql_table('clients', connection, schema='harvest',
                                    index_col='id')

        people = pd.read_sql_table('users', connection, schema='harvest',
                                   index_col='id')

        time_entries = pd.read_sql_table('time_entries', connection, schema='harvest',
                                         index_col='id',
                                         parse_dates=['spent_date'])

        time_entries = pd.merge(time_entries, projects['client_id'], left_on='project_id', right_index=True, how='left')

        return time_entries, projects, tasks, clients, people

    def process_data(self):
        # remove empty columns
        self.time_entries.dropna(axis=1, inplace=True)
        self.projects.dropna(axis=1, inplace=True)
        self.tasks.dropna(axis=1, inplace=True)
        self.clients.dropna(axis=1, inplace=True)
        self.people.dropna(axis=1, inplace=True)

        # replace dots in column names with underscores
        self.time_entries.columns = self.time_entries.columns.str.replace('.', '_')
        self.projects.columns = self.projects.columns.str.replace('.', '_')
        self.tasks.columns = self.tasks.columns.str.replace('.', '_')
        self.clients.columns = self.clients.columns.str.replace('.', '_')
        self.people.columns = self.people.columns.str.replace('.', '_')

    def get_person_name(self, person_id):
        """Get the full name of someone from their person_id"""
        return self.people.loc[person_id, 'first_name'] + ' ' + self.people.loc[person_id, 'last_name']

    def get_person_id(self, first_name, last_name=None):
        """Get the person_id of someone from their first_name and last_name."""
        if last_name is None:
            person_id = self.people.loc[(self.people['first_name'] == first_name)]

            if len(person_id) != 1:
                raise ValueError('Could not unique person with name ' + first_name)

        else:
            person_id = self.people.loc[(self.people['first_name'] == first_name) &
                                        (self.people['last_name'] == last_name)]

            if len(person_id) != 1:
                raise ValueError('Could not unique person with name ' + first_name + ' ' + last_name)

        return person_id.index[0]

    def get_project_name(self, project_id):
        """Get the name of a project from its project_id"""
        return self.projects.loc[project_id, 'name']

    def get_project_id(self, project_name):
        """Get the id of a project from its name"""
        return self.projects.index[self.projects.name == project_name][0]

    def get_client_name(self, client_id):
        """Get the name of a project from its project_id"""
        return self.clients.loc[client_id, 'name']

    def get_client_id(self, client_name):
        """Get the id of a client from its name"""
        return self.clients.index[self.clients.name == client_name][0]

    def get_task_name(self, task_id):
        """Get the name of a client from its id"""
        return self.tasks.loc[task_id, 'name']

    def get_task_id(self, task_name):
        """Get the id of a task from its name"""
        return self.tasks.index[self.tasks.name == task_name][0]

    def get_name(self, id_value, id_type):
        """Get the name of an id based on the type of id it is. id_type can be
        'person', 'project' 'client', or 'task'."""
        if id_type == 'person' or id_type == 'user.id' or id_type == 'user_id':
            return self.get_person_name(id_value)
        elif id_type == 'project' or id_type == 'project.id' or id_type == 'project_id':
            return self.get_project_name(id_value)
        elif id_type == 'client' or id_type == 'client.id' or id_type == 'client_id':
            return self.get_client_name(id_value)
        elif id_type == 'task' or id_type == 'task.id' or id_type == 'task_id':
            return self.get_task_name(id_value)
        else:
            raise ValueError('id_type must be person, project, client or task')

    def get_id(self, name, name_type):
        """Get the name of an id based on the type of id it is. id_type can be
        'person', 'project' 'client', or 'task'."""
        if name_type == 'person':
            return self.get_person_id(name.split(' ')[0], ' '.join(name.split(' ')[1:]))
        elif name_type == 'project':
            return self.get_project_id(name)
        elif name_type == 'client':
            return self.get_client_id(name)
        elif name_type == 'task':
            return self.get_task_id(name)
        else:
            raise ValueError('id_type must be person, project, client or task')

    def get_entries(self, id_column, ref_column):
        """For each unique value in id_column, create a dataframe where the rows are dates,
        the columns are projects/people/clients/tasks depending on id_column, and the values are
        time allocations for each project/person/client/task for each date.
        id_column can be 'person', 'project', 'client', or 'task'
        ref_column can be 'person', 'project', 'client', 'task' or 'TOTAL' but must not be same as id_column."""

        if ref_column == id_column:
            raise ValueError('id_column and ref_column must be different.')

        # id column
        if id_column == 'person':
            id_column = 'user_id'
            id_values = self.people.index

        elif id_column == 'project':
            id_column = 'project_id'
            id_values = self.projects.index

        elif id_column == 'client':
            id_column = 'client_id'
            id_values = self.clients.index

        elif id_column == 'task':
            id_column = 'task_id'
            id_values = self.tasks.index

        else:
            raise ValueError('id_column must be person, project, client or task')

        # ref_column
        if ref_column == 'person':
            ref_column = 'user_id'

        elif ref_column == 'project':
            ref_column = 'project_id'

        elif ref_column == 'client':
            ref_column = 'client_id'

        elif ref_column == 'task':
            ref_column = 'task_id'

        elif ref_column != 'TOTAL':
            raise ValueError('id_column must be person, project, client, task or TOTAL')

        # group time_entries by id_column, ref_column and spent_date
        if ref_column == 'TOTAL':
            grouped_entries = self.time_entries.groupby([id_column, 'spent_date']).hours.sum()
        else:
            grouped_entries = self.time_entries.groupby([id_column, ref_column, 'spent_date']).hours.sum()

        # populate the entries dict from grouped_entries
        # entries is a dict with id_column values as keys and the items being a dataframe with ref_column as the index
        entries = {}

        for idx in id_values:
            # check whether the this id has any time entries, i.e. whether the id
            # exists in the index (get_level_values to deal with MultiIndex)
            if idx in grouped_entries.index.get_level_values(0):
                # get the allocations
                id_entries = grouped_entries.loc[idx]

                # unstack the MultiIndex
                id_entries = id_entries.reset_index()

                # Initialise dataframe to store results
                if ref_column == 'TOTAL':
                    id_entry_days = pd.Series(index=self.date_range)
                else:
                    id_entry_days = pd.DataFrame(index=self.date_range, columns=id_entries[ref_column].unique())

                id_entry_days.fillna(0, inplace=True)

                # Loop over each time entry
                for _, row in id_entries.iterrows():
                    if ref_column == 'TOTAL':
                        id_entry_days.loc[row['spent_date']] += row['hours']
                    else:
                        id_entry_days.loc[row['spent_date'], row[ref_column]] += row['hours']

            else:
                # no projects, just make an empty dataframe
                if ref_column == 'TOTAL':
                    id_entry_days = pd.Series(index=self.date_range).fillna(0)
                else:
                    id_entry_days = pd.DataFrame(index=self.date_range)

            # Add the person's name as a label - just nice for printing later.
            if ref_column != 'TOTAL':
                id_entry_days.columns.name = self.get_name(idx, id_column)

            entries[idx] = id_entry_days

        if ref_column == 'TOTAL':
            entries = pd.DataFrame(entries)

        return entries
