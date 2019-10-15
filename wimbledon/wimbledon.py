import pandas as pd
import holidays
from copy import deepcopy
import sqlalchemy as sqla
import os.path
import subprocess
import re
import numpy as np

import wimbledon.config
import wimbledon.harvest.db_interface
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
    def __init__(self,
                 conn=None, update_db=False,
                 with_tracked_time=True,
                 work_hrs_per_day=None,
                 proj_hrs_per_day=None):
        """Load and group Wimbledon data.
        
        Keyword Arguments:
            update_db {bool} -- update the database before loading data (default: {False})
            work_hrs_per_day {numeric} -- hours in normal working day (default: 8)
            proj_hrs_per_day {numeric} -- nominal hours spent on projects per day (default: 6.4)
            conn {SQLAlchemy connection} -- connection to database (default: get from wimbledon config)
            with_tracked_time {bool} -- whether to load and process timesheet data (default: {True})
        """
        if update_db:
            wimbledon.harvest.db_interface.update_db(
                conn=conn,
                with_tracked_time=with_tracked_time
            )

        data = query_db.get_data(conn=conn,
                                 with_tracked_time=with_tracked_time)
        self.people = data['people']
        self.projects = data['projects']
        self.assignments = data['assignments']
        self.clients = data['clients']
        self.associations = data['associations']
        
        start_date = self.assignments['start_date'].min()
        end_date = self.assignments['end_date'].max()

        if with_tracked_time:
            self.tasks = data['tasks']
            self.time_entries = data['time_entries']
                   
            start_date = min([start_date, self.time_entries['date'].min()])
            end_date = max([end_date, self.time_entries['date'].max()])
            # people may track time on non-working days, so create a separate
            # time series for time tracking
            self.date_range_alldays = pd.date_range(start=start_date,
                                                    end=end_date,
                                                    freq='D')
          
        # Find the earliest and latest date in the data, create a range
        # of weekdays between these dates (so people will only have allocations
        # to projects on working days)
        # NB: this should take into account bank holidays, but not things like
        # British Library shutdown over Christmas.
        self.date_range_workdays = get_business_days(start_date, end_date)

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

        # convert assignments in seconds per day to fractions of 1 FTE (defined by self.work_hrs_per_day)
        self.assignments['allocation'] = (self.assignments['allocation'] /
                                          (self.work_hrs_per_day * 60 * 60))
        
        # convert baseline capacity in seconds per week to fraction of 1 FTE
        self.people.capacity = (self.people.capacity /
                                (5 * self.work_hrs_per_day * 60 * 60))
        
        # people_allocations: dict with key person_id, contains df of (date, project_id) with allocation
        # people_totals: df of (date, person_id) with total allocations
        self.people_allocations, self.people_totals = self.__get_allocations('person')
       
        # resource required, unconfirmed, deferred allocations
        self.resourcereq_allocations = self.get_person_allocations('RESOURCE REQUIRED')
        self.unconfirmed_allocations = self.get_person_allocations('UNCONFIRMED')
        self.deferred_allocations = self.get_person_allocations('DEFERRED')
 
        # calculate team capacity: capacity in people table minus any allocations to unavailable project
        unavailable_id = self.get_project_id('UNAVAILABLE')
        
        self.people_capacities = pd.DataFrame(index=self.date_range_workdays,
                                              columns=self.people.index)

        for person_id in self.people.index:
            self.people_capacities[person_id] = self.people.capacity[person_id]
            
            if unavailable_id in self.people_allocations[person_id].columns:
                self.people_capacities[person_id] = (
                    self.people_capacities[person_id] -
                    self.people_allocations[person_id][unavailable_id]
                )

        self.team_capacity = self.people_capacities.sum(axis=1)

        self.people_free_capacity = self.people_capacities - self.people_totals
        
        # project_allocations: dict with key project_id, contains df of (date, person_id) with allocation
        # project_confirmed: df of (date, project_id) with total allocations across PEOPLE ONLY
        self.project_allocations, self.project_confirmed = self.__get_allocations('project')

        # project_unconfirmed: df of (date, project_id) with total allocation to unconfirmed placeholders
        self.project_unconfirmed = self.__get_project_unconfirmed()

        # project_deferred:  df of (date, project_id) with total allocation to deferred placeholders
        self.project_deferred = self.__get_project_deferred()

        # project_resourcereq: resource_required allocations to each project
        self.project_resourcereq = self.__get_project_required()

        # project_confirmed: should not include unconfirmed or deferred totals
        self.project_confirmed = (self.project_confirmed -
                                  self.project_unconfirmed -
                                  self.project_deferred)

        self.project_allocated = (self.project_confirmed -
                                  self.project_resourcereq)

        # Time Tracking
        if with_tracked_time:
            self.tracked_project_tasks = self.__get_tracking('project', 'task')
            self.tracked_project_people = self.__get_tracking('project', 'person')
            self.tracked_person_projects = self.__get_tracking('person', 'project')
            self.tracked_person_tasks = self.__get_tracking('person', 'task')

            self.tracked_project_totals = self.__get_tracking('project', 'TOTAL')
            self.tracked_person_totals = self.__get_tracking('person', 'TOTAL')
            self.tracked_task_totals = self.__get_tracking('task', 'TOTAL')

            # calculate per-client totals for each person
            self.tracked_person_clients = self.__client_from_project_tracking(
                                            self.tracked_person_projects
                                        )

            # calculate overall per-client totals
            self.tracked_client_totals = self.__client_from_project_tracking(
                                            self.tracked_project_totals
                                        )

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

    def get_client_name(self, client_id):
        """Get the name of a project from its project_id"""
        return self.clients.loc[client_id, 'name']
    
    def get_client_id(self, client_name):
        return self.clients.index[self.clients.name == client_name][0]

    def get_task_name(self, task_id):
        """Get the name of a task from its id"""
        return self.tasks.loc[task_id, 'name']

    def get_task_id(self, task_name):
        """Get the id of a task from its name"""
        return self.tasks.index[self.tasks.name == task_name][0]

    def get_association_name(self, association_id):
        """get the association name from the association id"""
        return self.associations.loc[association_id, 'name']
    
    def get_association_id(self, association_name):
        """get the association id from the association name"""
        return self.associations.index[self.associations.name == association_name][0]
        
    def get_name(self, id_value, id_type):
        """Get the name of an id based on the type of id it is. id_type can be
        'person', 'project', 'client', or 'task'"""
        if id_type == 'person':
            return self.get_person_name(id_value)
        elif id_type == 'project':
            return self.get_project_name(id_value)
        elif id_type == 'client':
            return self.get_client_name(id_value)
        elif id_type == 'task':
            return self.get_task_name(id_value)
        else:
            raise ValueError('id_type must be person, project, client or task')

    def get_person_allocations(self, name):
        idx = self.get_person_id(name)
        return self.people_allocations[idx]

    def get_id(self, name, id_type):
        """Get the name of an id based on the type of id it is. id_type can be
        'person', 'project' or 'client', or 'task'."""
        if id_type == 'person':
            return self.get_person_id(name)

        elif id_type == 'project':
            return self.get_project_id(name)
        
        elif id_type == 'client':
            return self.get_client_id(name)

        elif id_type == 'task':
            return self.get_task_id(name)
        
        else:
            raise ValueError('id_type must be person or project')

    def whiteboard(self, key_type, start_date, end_date, freq):
        """Create the raw, unstyled, whiteboard visualisation.

            Dataframe with the rows being key_type (project or person ids), the columns
        dates and the cell values being either a person or project and their time allocation, sorted by time allocation.
]       """
        # TODO move this function somewhere else?
        if key_type == 'project':
            # copy to prevent overwriting original
            data_dict = deepcopy(self.project_allocations)

        elif key_type == 'person':
            data_dict = deepcopy(self.people_allocations)

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

                df.columns = [self.get_name(person_id, 'person')
                                for person_id in df.columns]
                
                df.columns.name = self.get_name(key, 'project')

            elif key_type == 'person':
                df.columns = [self.get_name(project_id, 'project')
                                for project_id in df.columns]

                df.columns.name = self.get_name(key, 'person')

            else:
                return ValueError('key type must be person or project')

            # add "AVAILABLE" for people with free capacity
            if key_type == 'person':
                df['UNALLOCATED'] = self.people_free_capacity[key]

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

                # sort columns by magnitude of earliest assignment
                df = df.sort_values(by=[idx for idx in df.index],
                                    axis=1,
                                    ascending=False)

                # max number items assigned to this key at a time
                n_columns = (df > 0).sum(axis=1).max()

                # initialise data frame to store ranked time assignments
                key_sheet = pd.DataFrame('',
                                            index=df.index,
                                            columns=range(1, n_columns + 1))

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
                [key_sheet.drop(col, axis=1, inplace=True)
                    for col in key_sheet.columns
                    if key_sheet[col].str.len().sum() == 0]

                # format dates nicely
                if freq == 'MS':
                    key_sheet = pd.DataFrame(key_sheet,
                                                index=key_sheet.index.strftime("%b-%Y"))
                elif freq == 'W-MON':
                    key_sheet = pd.DataFrame(key_sheet,
                                                index=key_sheet.index.strftime("%d-%b-%Y"))
                else:
                    key_sheet = pd.DataFrame(key_sheet,
                                                index=key_sheet.index.strftime("%Y-%m-%d"))

                # store the allocations - transpose to get rows as keys and columns as dates
                sheet[df.columns.name] = key_sheet.T

        # merge everything together into one large dataframe, sorted by key
        sheet = pd.concat(sheet).sort_index()

        if key_type == 'project':

            # Get project client names
            proj_idx = [self.get_project_id(name)
                        for name in sheet.index.get_level_values(0)]
            client_idx = self.projects.loc[proj_idx, 'client']
            client_name = self.clients.loc[client_idx, 'name']

            # Add project client info to index (~programme area)
            sheet['client_name'] = client_name.values
            sheet.set_index(['client_name', sheet.index], inplace=True)
            sheet.index.rename('project_name', 1, inplace=True)
            sheet.index.rename('row', 2, inplace=True)

            sheet.sort_values(by=['client_name', 'project_name', 'row'],
                                inplace=True)
            
            # Move REG projects to end
            clients = client_name.unique()
            reg = sorted([client for client in clients
                            if 'REG' in client])
            others = sorted([client for client in clients
                                if 'REG' not in client])
            sheet = sheet.reindex(others+reg, level=0)

            # Remove index headings
            sheet.index.rename([None, None, None], inplace=True)

            # Get GitHub issue numbers, add as hrefs
            proj_names = sheet.index.levels[1].values
            proj_idx = [self.get_project_id(name)
                        for name in proj_names]
            proj_gitissue = [self.projects.loc[idx, 'github']
                                for idx in proj_idx]
            git_base_url = 'https://github.com/alan-turing-institute/Hut23/issues'

            proj_names_with_url = {}
            for idx, proj in enumerate(proj_names):
                if not np.isnan(proj_gitissue[idx]):
                    proj_names_with_url[proj] = """<a href="{url}/{issue}">{proj}<br>[GitHub: #{issue}]</a>""".format(url=git_base_url,
                                                                                                issue=int(proj_gitissue[idx]),
                                                                                                proj=proj)

            sheet.rename(proj_names_with_url, axis='index', level=1, inplace=True)

        elif key_type == 'person':

            # Get person association group
            person_idx = [self.get_person_id(name)
                            for name in sheet.index.get_level_values(0)]

            assoc_idx = [self.people.loc[idx, 'association']
                            for idx in person_idx]
            
            group_name = [self.associations.loc[idx, 'name']
                            for idx in assoc_idx]

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

    def __get_allocations(self, id_column):
        """For each unique value in id_column, create a dataframe where
        the rows are dates, the columns are projects/people depending on
        id_column, and the values are time allocations for that date.
        id_column can be 'person' or 'project'."""
        if id_column == 'person':
            grouped_allocations = self.assignments.groupby(
                ['person', 'project', 'start_date', 'end_date']).allocation.sum()
            id_values = self.people.index
            ref_column = 'project'

        elif id_column == 'project':
            grouped_allocations = self.assignments.groupby(
                ['project', 'person', 'start_date', 'end_date']).allocation.sum()
            id_values = self.projects.index
            ref_column = 'person'

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
                id_alloc_days = pd.DataFrame(index=self.date_range_workdays,
                                             columns=id_allocs[ref_column].unique())
                id_alloc_days.fillna(0, inplace=True)

                # Loop over each assignment
                for _, row in id_allocs.iterrows():
                    # Create the range of business days that this assignment
                    # corresponds to
                    dates = get_business_days(row['start_date'],
                                              row['end_date'])

                    # Add the allocation to the corresponding project for the
                    # range of dates.
                    id_alloc_days.loc[dates, row[ref_column]] += row['allocation']

            else:
                # no projects, just make an empty dataframe
                id_alloc_days = pd.DataFrame(index=self.date_range_workdays)

            # Add the person's name as a label - just nice for printing later.
            id_alloc_days.columns.name = self.get_name(idx, id_column)

            allocations[idx] = id_alloc_days

        # total assignment each day
        totals = pd.DataFrame(index=self.date_range_workdays, columns=id_values)
        for idx in allocations.keys():
            unavailable_id = self.get_project_id('UNAVAILABLE')
            if (ref_column == 'project' and
                unavailable_id in allocations[idx].columns):
                # don't include unavailable project in totals
                totals[idx] = allocations[idx].\
                    drop(unavailable_id, axis=1).\
                    sum(axis=1)
            else:
                totals[idx] = allocations[idx].sum(axis=1)

        return allocations, totals

    def __get_project_unconfirmed(self):
        """Get unconfirmed project requirements"""

        unconf_idx = self.get_person_id('UNCONFIRMED')

        project_unconfirmed = pd.DataFrame(0,
                                           index=self.date_range_workdays,
                                           columns=self.projects.index)

        allocs = self.people_allocations[unconf_idx]

        for project in allocs.columns:
            project_unconfirmed[project] += allocs[project]

        return project_unconfirmed

    def __get_project_deferred(self):
        """Get deferred project allocations"""

        defer_idx = self.get_person_id('DEFERRED')

        project_deferred = pd.DataFrame(0,
                                        index=self.date_range_workdays,
                                        columns=self.projects.index)

        allocs = self.people_allocations[defer_idx]

        for project in allocs.columns:
            project_deferred[project] += allocs[project]

        return project_deferred

    def __get_project_required(self):
        """Get resource required (i.e. needs someone assigned)
        for all projects."""

        resreq_idx = self.get_person_id('RESOURCE REQUIRED')

        project_resreq = pd.DataFrame(0,
                                      index=self.date_range_workdays,
                                      columns=self.projects.index)

        allocs = self.people_allocations[resreq_idx]

        for project in allocs.columns:
            project_resreq[project] += allocs[project]

        return project_resreq

    def __get_tracking(self, id_column, ref_column):
        """For each unique value in id_column, create a dataframe where the rows are dates,
        the columns are projects/people/clients/tasks depending on id_column, and the values are
        tracked time for each project/person/client/task for each date.
        id_column can be 'person', 'project', 'client', or 'task'
        ref_column can be 'person', 'project', 'client', 'task' or 'TOTAL' but must not be same as id_column."""

        if ref_column == id_column:
            raise ValueError('id_column and ref_column must be different.')

        # id column
        if id_column == 'person':
            id_values = self.people.index

        elif id_column == 'project':
            id_values = self.projects.index

        elif id_column == 'client':
            id_values = self.clients.index

        elif id_column == 'task':
            id_values = self.tasks.index
        else:
            raise ValueError('id_column must be person, project, client or task')

        # ref_column
        if ref_column not in ['person', 'project', 'client', 'task', 'TOTAL']:
            raise ValueError("""id_column must be person, project, client,
                             task or TOTAL""")

        # group time_entries by id_column, ref_column and date
        if ref_column == 'TOTAL':
            grouped_entries = self.time_entries.groupby([id_column, 'date']).hours.sum()
        else:
            grouped_entries = self.time_entries.groupby([id_column, ref_column, 'date']).hours.sum()

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
                    id_entry_days = pd.Series(index=self.date_range_alldays)
                else:
                    id_entry_days = pd.DataFrame(index=self.date_range_alldays,
                                                 columns=id_entries[ref_column].unique())

                id_entry_days.fillna(0, inplace=True)

                # Loop over each time entry
                for _, row in id_entries.iterrows():
                    if ref_column == 'TOTAL':
                        id_entry_days.loc[row['date']] += row['hours']
                    else:
                        id_entry_days.loc[row['date'], row[ref_column]] += row['hours']

            else:
                # no projects, just make an empty dataframe
                if ref_column == 'TOTAL':
                    id_entry_days = pd.Series(index=self.date_range_alldays).fillna(0)
                else:
                    id_entry_days = pd.DataFrame(index=self.date_range_alldays)

            # Add the person's name as a label - just nice for printing later.
            if ref_column != 'TOTAL':
                id_entry_days.columns.name = self.get_name(idx, id_column)

            entries[idx] = id_entry_days

        if ref_column == 'TOTAL':
            entries = pd.DataFrame(entries)

        return entries

    def __client_from_project_tracking(self, tracking):
        """Group previously calculated project tracking values by client.
        
        Arguments:
            tracking {pd.DataFrame or dict} -- a single dataframe or a dict of
            dataframes containing project ids as columns.
        
        Raises:
            TypeError: if tracking is not an instance of pd.DataFrame or dict.
        
        Returns:
            pd.DataFrame or dict -- same format as tracking except with columns
            now being client ids.
        """
        if isinstance(tracking, pd.DataFrame):
            grouped_df = tracking.copy(deep=True)
                
            grouped_df.columns = [
                    self.projects.loc[col, 'client']
                    for col in grouped_df.columns
                ]
            grouped_df = grouped_df.\
                groupby(grouped_df.columns, axis=1).\
                sum()
            return grouped_df
                    
        elif isinstance(tracking, dict):
            grouped_dict = dict()
            for idx, df in tracking.items():
                grouped_df = df.copy(deep=True)
                
                grouped_df.columns = [
                        self.projects.loc[col, 'client']
                        for col in grouped_df.columns
                    ]
                grouped_df = grouped_df.\
                    groupby(grouped_df.columns, axis=1).\
                    sum()
                grouped_dict[idx] = grouped_df
            
            return grouped_dict
        else:
            raise TypeError('tracking must be dataframe or dict of dataframes')
