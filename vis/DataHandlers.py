import pandas as pd
import holidays
from copy import deepcopy
import sqlalchemy as sqla
import os.path
import json
import subprocess


def get_business_days(start_date, end_date):
    """Get a daily time series between start_date and end_date excluding weekends and public holidays."""

    date_range = pd.date_range(start=start_date,
                               end=end_date,
                               freq=pd.tseries.offsets.BDay())

    # remove public holidays
    pub_hols = holidays.England()
    date_range = pd.to_datetime([date for date in date_range if date not in pub_hols])

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


class Forecast:
    """Load and group Forecast data"""
    def __init__(self, data_source='csv', hrs_per_day=None):
        # 1 FTE hours per day for projects
        if hrs_per_day is None:
            self.hrs_per_day = 8
        else:
            self.hrs_per_day = hrs_per_day

        if data_source == 'csv':
            self.people, self.projects, self.placeholders, self.assignments, self.clients, self.date_range = self.load_csv_data()
        elif data_source == 'sql':
            self.people, self.projects, self.placeholders, self.assignments, self.clients, self.date_range = self.load_sql_data()
        else:
            raise ValueError('data_source must be csv or sql')

        self.people_allocations, self.people_totals = self.get_allocations('person')

        self.project_allocations, self.project_totals = self.get_allocations('project')

        self.placeholder_allocations, self.placeholder_totals = self.get_allocations('placeholder')

        self.project_reqs, self.project_netalloc = self.get_project_required()

    def load_csv_data(self):
        """load data from csv files in ../data/forecast directory"""

        people = pd.read_csv('../data/forecast/people.csv',
                             index_col='id',
                             parse_dates=['updated_at'],
                             infer_datetime_format=True)

        # assign missing capacities as 1 FTE, given by self.hrs_per_day, 5 days per week
        people['weekly_capacity'].fillna(self.hrs_per_day * 5 * 60 * 60, inplace=True)

        # convert capacity into FTE at self.hrs_per_day hours per day
        people['weekly_capacity'] = people['weekly_capacity'] / (self.hrs_per_day * 5 * 60 * 60)

        # remove project managers
        people = people[people.roles != "['Research Project Manager']"]

        projects = pd.read_csv('../data/forecast/projects.csv',
                               index_col='id',
                               parse_dates=['updated_at', 'start_date', 'end_date'],
                               infer_datetime_format=True)

        placeholders = pd.read_csv('../data/forecast/placeholders.csv',
                                   index_col='id',
                                   parse_dates=['updated_at'],
                                   infer_datetime_format=True)

        assignments = pd.read_csv('../data/forecast/assignments.csv',
                                  index_col='id',
                                  parse_dates=['start_date', 'end_date', 'updated_at'],
                                  infer_datetime_format=True)

        clients = pd.read_csv('../data/forecast/clients.csv',
                              index_col='id',
                              parse_dates=['updated_at'],
                              infer_datetime_format=True)

        # convert assignments in seconds per day to fractions of 1 FTE (defined by self.hrs_per_day)
        assignments['allocation'] = assignments['allocation'] / (self.hrs_per_day * 60 * 60)

        # Find the earliest and latest date in the data, create a range of weekdays between these dates
        date_range = get_business_days(assignments['start_date'].min(), assignments['end_date'].max())

        return people, projects, placeholders, assignments, clients, date_range

    def load_sql_data(self):
        """load data from sql database defined by ../sql/config.json, which must be a json containing
        host: the server name (url)
        database: the name of the database on the server
        drivername: the type of database it is, e.g. postgresql"""

        with open('../sql/config.json', 'r') as f:
            config = json.load(f)

        if config['host'] == 'localhost':
            url = sqla.engine.url.URL(drivername=config['drivername'],
                                      host=config['host'],
                                      database=config['database'])

            subprocess.call(['sh', '../sql/start_localhost.sh'], cwd='../sql')

        else:
            with open(os.path.expanduser("~/.pgpass"), 'r') as f:
                secrets = None
                for line in f:
                    if config['host'] in line:
                        secrets = line.strip().split(':')
                        break

            if secrets is None:
                raise ValueError('did not find ' + config.wimbledon_config['host'] + ' in ~/.pgpass')

            url = sqla.engine.url.URL(drivername=config['drivername'],
                                      username=secrets[-2],
                                      password=secrets[-1],
                                      host=config['host'],
                                      database=config['database'])

        engine = sqla.create_engine(url)

        connection = engine.connect()

        people = pd.read_sql_table('people', connection, schema='forecast',
                                   index_col='id')

        # assign missing capacities as 1 FTE, given by self.hrs_per_day, 5 days per week
        people['weekly_capacity'].fillna(self.hrs_per_day * 5 * 60 * 60, inplace=True)

        # convert capacity into FTE at self.hrs_per_day hours per day
        people['weekly_capacity'] = people['weekly_capacity'] / (self.hrs_per_day * 5 * 60 * 60)

        # remove project managers
        people = people[people.role != "['Research Project Manager']"]

        clients = pd.read_sql_table('clients', connection, schema='forecast',
                                    index_col='id')

        projects = pd.read_sql_table('projects', connection, schema='forecast',
                                     index_col='id',
                                     parse_dates=['start_date', 'end_date'])

        placeholders = pd.read_sql_table('placeholders', connection, schema='forecast',
                                         index_col='id')

        assignments = pd.read_sql_table('assignments', connection, schema='forecast',
                                        index_col='id',
                                        parse_dates=['start_date', 'end_date'])

        # convert assignments in seconds per day to fractions of 1 FTE (defined by self.hrs_per_day)
        assignments['allocation'] = assignments['allocation'] / (self.hrs_per_day * 60 * 60)

        # Find the earliest and latest date in the data, create a range of weekdays between these dates
        date_range = get_business_days(assignments['start_date'].min(), assignments['end_date'].max())

        return people, projects, placeholders, assignments, clients, date_range

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
            person_id = self.people.loc[(self.people['first_name'] == first_name) & (self.people['last_name'] == last_name)]

            if len(person_id) != 1:
                raise ValueError('Could not unique person with name ' + first_name + ' ' + last_name)

        return person_id.index[0]

    def get_project_name(self, project_id):
        """Get the name of a project from its project_id"""
        return self.projects.loc[project_id, 'name']

    def get_project_id(self, project_name):
        """Get the id of a project from its name"""
        return self.projects.index[self.projects.name == project_name][0]

    def get_harvest_id(self, forecast_id):
        """get the harvest id of a forecast project."""
        return self.projects.loc[forecast_id, 'harvest_id']

    def get_placeholder_name(self, placeholder_id):
        """Get the name of a placeholder from its id"""
        return self.placeholders.loc[placeholder_id, 'name']

    def get_placeholder_id(self, placeholder_name):
        """Get the id of a placeholder from its name"""
        return self.placeholders.index[self.placeholders.name == placeholder_name][0]

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
        elif id_type == 'placeholder':
            return self.get_placeholder_name(id_value)
        else:
            raise ValueError('id_type must be person, project or placeholder')

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

        elif id_column == 'placeholder':
            grouped_allocations = self.assignments.groupby(
                ['placeholder_id', 'project_id', 'start_date', 'end_date']).allocation.sum()
            id_values = self.placeholders.index
            ref_column = 'project_id'

        else:
            raise ValueError('id_column must be person, project or placeholder')

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

        project_unconfirmed = self.project_totals.copy(deep=True)
        project_unconfirmed[:] = 0

        for idx in project_unconf_ids:
            allocs = self.placeholder_allocations[idx]

            for col in allocs.columns:
                project_unconfirmed[col] += allocs[col]

        return project_unconfirmed

    def get_project_deferred(self):
        """Get deferred project allocations"""

        project_defer_ids = self.placeholders[self.placeholders.name.str.lower().str.contains('deferred')].index

        project_deferred = self.project_totals.copy(deep=True)
        project_deferred[:] = 0

        for idx in project_defer_ids:
            allocs = self.placeholder_allocations[idx]

            for col in allocs.columns:
                project_deferred[col] += allocs[col]

        return project_deferred

    def get_project_required(self):
        """Get amount of additional resource that needs to be required over time, i.e. difference between
        project requirements and project allocations."""
        # Project requirements = Project assignments + Resource required assignments
        project_reqs = self.project_totals.copy(deep=True)

        # add resource req info from placeholders
        resource_req_ids = []
        for idx in self.placeholders.index:
            name = self.placeholders.loc[idx, 'name'].lower()

            if 'deferred' in name or 'unconfirmed' in name:
                continue
            else:
                resource_req_ids.append(idx)

        for idx in resource_req_ids:
            allocs = self.placeholder_allocations[idx]

            for col in allocs.columns:
                project_reqs[col] += allocs[col]

        project_netalloc = project_reqs - self.project_totals

        return project_reqs, project_netalloc

    def spreadsheet_sheet(self, key_type, start_date, end_date, freq, add_placeholders=True):
        """Create a spreadsheet style dataframe with the rows being key_type (project or person ids), the columns
        dates and the cell values being either a person or project and their time allocation, sorted by time allocation.
        If add_placeholders=True, non-resource required placeholders will be included on the sheet."""

        if key_type == 'project':
            # copy to prevent overwriting original
            data_dict = deepcopy(self.project_allocations)

            mask = (self.project_netalloc.index >= start_date) & (self.project_netalloc.index <= end_date)
            resreq = self.project_netalloc.loc[mask]

            if add_placeholders:
                # add placeholders to data_dict, excluding resource required placeholders
                placeholder_ids = [idx for idx in self.placeholders.index
                                   if 'resource required' not in self.placeholders.loc[idx, 'name'].lower()]

                for placeholder_id in placeholder_ids:
                    for project_id in self.placeholder_allocations[placeholder_id].columns:
                        data_dict[project_id].loc[:, placeholder_id] = self.placeholder_allocations[placeholder_id][project_id]

        elif key_type == 'person':
            data_dict = self.people_allocations

            if add_placeholders:
                # add placeholders to data_dict, excluding resource required placeholders
                placeholder_ids = [idx for idx in self.placeholders.index
                                   if 'resource required' not in self.placeholders.loc[idx, 'name'].lower()]

                for idx in placeholder_ids:
                    data_dict[idx] = self.placeholder_allocations[idx]

        else:
            return ValueError('key type must be person or project')

        sheet = {}

        # set of unique project names used for cell colouring later
        names = set()

        # for each project
        for key in data_dict.keys():

            # get the projects's person allocations
            df = data_dict[key]

            # extract the date range of interest
            df = select_date_range(df, start_date, end_date)

            # check there are project allocations to display
            rows, cols = df.shape
            if rows > 0 and cols > 0:

                # replace ids with names. for project id: include resource required.
                if key_type == 'project':
                    df.columns = [self.get_name(person_id, 'person') for person_id in df.columns]
                    df.columns.name = self.get_name(key, 'project')
                    df['RESOURCE REQUIRED'] = resreq[key]

                elif key_type == 'person':
                    df.columns = [self.get_name(project_id, 'project') for project_id in df.columns]
                    df.columns.name = self.get_name(key, 'person')

                else:
                    return ValueError('key type must be person or project')

                # update the set of names
                [names.add(col) for col in df.columns]

                # resample the data to the given date frequency
                if freq != 'D':
                    df = df.resample(freq).mean()

                # max number items assigned to this key at a time
                n_columns = (df > 0).sum(axis=1).max()

                # initialise data frame to store projects/people ranked by time assignment
                df_ranked = pd.DataFrame(index=df.index, columns=range(1, n_columns + 1))

                # for each date period
                for date in df_ranked.index:

                    # rank the items for this date period by time allocation
                    sorted_df = df.loc[date, df.loc[date] > 0].sort_values(ascending=False)

                    if len(sorted_df) > 0:
                        for i in range(len(sorted_df)):
                            # Fill with format <NAME> (<ALLOCATION>)
                            df_ranked.loc[date, i + 1] = sorted_df.index[i] + '<br>({:.1f})'.format(sorted_df.iloc[i])

                        # empty strings for unused ranks
                        df_ranked.loc[date, range(len(sorted_df) + 1, n_columns + 1)] = ''

                    else:
                        df_ranked.loc[date, :] = ''

                # remove unused columns
                [df_ranked.drop(col, axis=1, inplace=True) for col in df_ranked.columns if
                 df_ranked[col].str.len().sum() == 0]

                # format dates nicely
                if freq == 'MS':
                    df_ranked = pd.DataFrame(df_ranked, index=df_ranked.index.strftime("%b-%Y"))
                elif freq == 'W-MON':
                    df_ranked = pd.DataFrame(df_ranked, index=df_ranked.index.strftime("%d-%b-%Y"))
                else:
                    df_ranked = pd.DataFrame(df_ranked, index=df_ranked.index.strftime("%Y-%m-%d"))

                # store the allocations - transpose to get rows as keys and columns as dates
                try:
                    sheet[self.get_name(key, key_type)] = df_ranked.T
                except KeyError:
                    sheet[self.get_name(key, 'placeholder')] = df_ranked.T

        # merge everything together into one large dataframe, sorted by key
        sheet = pd.concat(sheet).sort_index()

        if key_type == 'project':
            # Add project client info to index (~programme area)
            proj_idx = [self.get_project_id(name) for name in sheet.index.get_level_values(0)]
            client_idx = self.projects.loc[proj_idx, 'client_id']
            client_name = self.clients.loc[client_idx, 'name']

            sheet['client_name'] = client_name.values
            sheet.set_index(['client_name', sheet.index], inplace=True)
            sheet.index.rename('project_name', 1, inplace=True)
            sheet.index.rename('rank', 2, inplace=True)
            sheet.sort_values(by=['client_name', 'project_name', 'rank'], inplace=True)
            sheet.index.rename([None, None, None], inplace=True)

        return sheet


class Harvest:
    """Load and group Harvest data"""

    def __init__(self, data_source='csv', proj_hrs_per_day=None):
        self.data_source = data_source

        if proj_hrs_per_day is None:
            self.proj_hrs_per_day = 6.4
        else:
            self.proj_hrs_per_day = proj_hrs_per_day

        if data_source == 'csv':
            self.time_entries, self.projects, self.tasks, self.clients, self.people, self.date_range = self.load_csv_data()
        elif data_source == 'sql':
            self.time_entries, self.projects, self.tasks, self.clients, self.people, self.date_range = self.load_sql_data()
        else:
            raise ValueError('data_source must be csv or sql')

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

    def load_csv_data(self):
        time_entries = pd.read_csv('../data/harvest/time_entries.csv',
                                   index_col='id',
                                   parse_dates=['created_at', 'spent_date', 'updated_at',
                                                'task_assignment.created_at', 'task_assignment.updated_at',
                                                'user_assignment.created_at', 'user_assignment.updated_at'],
                                   infer_datetime_format=True)

        # remove empty columns
        time_entries.dropna(axis=1, inplace=True)

        projects = pd.read_csv('../data/harvest/projects.csv',
                               index_col='id',
                               parse_dates=['created_at', 'starts_on', 'ends_on', 'updated_at'],
                               infer_datetime_format=True)

        # remove empty columns
        projects.dropna(axis=1, inplace=True)

        tasks = pd.read_csv('../data/harvest/tasks.csv',
                            index_col='id',
                            parse_dates=['created_at', 'updated_at'],
                            infer_datetime_format=True)

        # remove empty columns
        tasks.dropna(axis=1, inplace=True)

        clients = pd.read_csv('../data/harvest/clients.csv',
                              index_col='id',
                              parse_dates=['created_at', 'updated_at'],
                              infer_datetime_format=True)

        # remove empty columns
        clients.dropna(axis=1, inplace=True)

        people = pd.read_csv('../data/harvest/users.csv',
                             index_col='id',
                             parse_dates=['created_at', 'updated_at'],
                             infer_datetime_format=True)

        people.dropna(axis=1, inplace=True)

        # Find the earliest and latest date in the data, create a range of weekdays between these dates
        # NB: Harvest data needs to include non-working days as there may be time entries on these days, e.g.
        # leave or block entering data for a month on the 1st of that month.
        date_range = pd.date_range(start=time_entries['spent_date'].min(),
                                   end=time_entries['spent_date'].max(),
                                   freq='D')

        return time_entries, projects, tasks, clients, people, date_range

    def load_sql_data(self):
        """load data from sql database defined by ../sql/config.json, which must be a json containing
        host: the server name (url)
        database: the name of the database on the server
        drivername: the type of database it is, e.g. postgresql"""

        with open('../sql/config.json', 'r') as f:
            config = json.load(f)

        if config['host'] == 'localhost':
            url = sqla.engine.url.URL(drivername=config['drivername'],
                                      host=config['host'],
                                      database=config['database'])

            subprocess.call(['sh', '../sql/start_localhost.sh'], cwd='../sql')

        else:
            with open(os.path.expanduser("~/.pgpass"), 'r') as f:
                secrets = None
                for line in f:
                    if config['host'] in line:
                        secrets = line.strip().split(':')
                        break

            if secrets is None:
                raise ValueError('did not find ' + config.wimbledon_config['host'] + ' in ~/.pgpass')

            url = sqla.engine.url.URL(drivername=config['drivername'],
                                      username=secrets[-2],
                                      password=secrets[-1],
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

        # Find the earliest and latest date in the data, create a range of weekdays between these dates
        # NB: Harvest data needs to include non-working days as there may be time entries on these days, e.g.
        # leave or block entering data for a month on the 1st of that month.
        date_range = pd.date_range(start=time_entries['spent_date'].min(),
                                   end=time_entries['spent_date'].max(),
                                   freq='D')

        return time_entries, projects, tasks, clients, people, date_range

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
            person_id = self.people.loc[(self.people['first_name'] == first_name) & (self.people['last_name'] == last_name)]

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
            if self.data_source == 'csv':
                id_column = 'user.id'
            elif self.data_source == 'sql':
                id_column = 'user_id'

            id_values = self.people.index

        elif id_column == 'project':
            if self.data_source == 'csv':
                id_column = 'project.id'
            elif self.data_source == 'sql':
                id_column = 'project_id'

            id_values = self.projects.index

        elif id_column == 'client':
            if self.data_source == 'csv':
                id_column = 'client.id'
            elif self.data_source == 'sql':
                id_column = 'client_id'

            id_values = self.clients.index

        elif id_column == 'task':
            if self.data_source == 'csv':
                id_column = 'task.id'
            elif self.data_source == 'sql':
                id_column = 'task_id'

            id_values = self.tasks.index

        else:
            raise ValueError('id_column must be person, project, client or task')

        # ref_column
        if ref_column == 'person':
            if self.data_source == 'csv':
                ref_column = 'user.id'
            elif self.data_source == 'sql':
                ref_column = 'user_id'

        elif ref_column == 'project':
            if self.data_source == 'csv':
                ref_column = 'project.id'
            elif self.data_source == 'sql':
                ref_column = 'project_id'

        elif ref_column == 'client':
            if self.data_source == 'csv':
                ref_column = 'client.id'
            elif self.data_source == 'sql':
                ref_column = 'client_id'

        elif ref_column == 'task':
            if self.data_source == 'csv':
                ref_column = 'task.id'
            elif self.data_source == 'sql':
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


