import wimbledon.config

import forecast
import harvest

import json
import requests

import pandas as pd
from pandas.io.json import json_normalize

import time

import os.path


def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


'''
!!!!!!!!!!!!!!!!!!!!!!!!!!!!! SQL !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'''

import sqlalchemy as sqla
import subprocess


def get_db_connection():
    config = wimbledon.config.get_sql_config()

    if config['host'] == 'localhost':
        url = sqla.engine.url.URL(drivername=config['drivername'],
                                  host=config['host'],
                                  database=config['database'])

        subprocess.call(['sh', '../sql/make_clean_db.sh', '--config', 'localhost'], cwd='../sql')

    else:
        with open(os.path.expanduser("~/.pgpass"), 'r') as f:
            sql_secrets = None
            for line in f:
                if config['host'] in line:
                    sql_secrets = line.strip().split(':')
                    break

        if sql_secrets is None:
            raise ValueError('did not find ' + config['host'] + ' in ~/.pgpass')

        url = sqla.engine.url.URL(drivername=config['drivername'],
                                  username=sql_secrets[-2],
                                  password=sql_secrets[-1],
                                  host=config['host'],
                                  database=config['database'])

        subprocess.call(['sh', '../sql/make_clean_db.sh', '--config', 'azure'], cwd='../sql')

    engine = sqla.create_engine(url)
    connection = engine.connect()

    return connection


# function to load csv and insert it to database
def df_to_sql(connection, schema, table_name,
              df, usecols, parse_dates, ints_with_nan):

    """
    Function to send df to database.
    schema: forecast or harvest
    table_name: name of table in database
    usecols: which columns from df to send to database
    parse_dates: which columns in usecols are dates
    ints_with_nan: which columns in usecols are integers but may be interpreted as floats due to missing values
    index_col: which column is the index
    """

    df = df[usecols]

    for col in ints_with_nan:
        # Integer columns with NaN: Requires pandas 0.24 (otherwise ids end up as floats)
        df[col] = df[col].astype('Int64')

    for col in parse_dates:
        df[col] = pd.to_datetime(df[col], infer_datetime_format=True)

    df.columns = df.columns.str.replace('.', '_')

    df.to_sql(table_name, connection, schema=schema, if_exists='append')


'''
!!!!!!!!!!!!!!!!!!!!!!!!!!!!! /SQL !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'''


def update_forecast(data_store='csv', connection=None):
    """
    Extract forecast data from its API using the pyforecast package.

    To install pyforecast, run:
    pip install pyforecast

    NB: The forecast API is not public and is undocumented. See:
    https://help.getharvest.com/forecast/faqs/faq-list/api/
    """
    if (data_store != 'csv') and (data_store != 'sql'):
        return ValueError('data_store must be csv or sql')

    start = time.time()

    if data_store == 'csv':
        check_dir('../data/forecast')

    secrets = wimbledon.config.get_harvest_credentials()

    api = forecast.Api(account_id=secrets.harvest_api_credentials['forecast_account_id'],
                       auth_token=secrets.harvest_api_credentials['access_token'])

    user = api.whoami()
    print()
    print('AUTHENTICATED USER:')
    print(user.first_name, user.last_name, user.email)
    print()

    def response_to_df(api_response):
        """Takes an api response in the pyforecast foremat and converts it into a pandas data frame."""
        results = [json.loads(result.to_json()) for result in api_response]

        df = json_normalize(results)
        df.set_index('id', inplace=True)

        return df

    print('CLIENTS')
    clients = response_to_df(api.get_clients(), title='CLIENTS')
    if data_store == 'csv':
        clients.to_csv('../data/forecast/clients.csv')
    else:
        df_to_sql(connection, 'forecast', 'clients', clients,
                  usecols=['name', 'harvest_id', 'archived'],
                  parse_dates=[],
                  ints_with_nan=['harvest_id'])

    print('PROJECTS')
    projects = response_to_df(api.get_projects(), title='PROJECTS')
    if data_store == 'csv':
        projects.to_csv('../data/forecast/projects.csv')
    else:
        df_to_sql(connection, 'forecast', 'projects', projects,
                  usecols=['name', 'code', 'start_date', 'end_date', 'client_id', 'harvest_id', 'notes', 'archived'],
                  parse_dates=['start_date', 'end_date'],
                  ints_with_nan=['client_id','harvest_id'])

    print('ROLES')
    roles = response_to_df(api.get_roles(), title='ROLES')
    if data_store == 'csv':
        roles.to_csv('../data/forecast/roles.csv')
    else:
        df_to_sql(connection, 'forecast', 'roles', roles,
                  usecols=['name', 'harvest_role_id'],
                  parse_dates=[],
                  ints_with_nan=['harvest_role_id'])

    print('PEOPLE')
    people = response_to_df(api.get_people(), title='PEOPLE')
    if data_store == 'csv':
        people.to_csv('../data/forecast/people.csv')
    else:
        df_to_sql(connection, 'forecast', 'people', people,
                  usecols=['first_name', 'last_name', 'email', 'harvest_user_id', 'login', 'subscribed',
                           'admin', 'archived', 'weekly_capacity', 'working_days.monday', 'working_days.tuesday',
                           'working_days.wednesday', 'working_days.thursday', 'working_days.friday',
                           'working_days.saturday', 'working_days.sunday'],
                  parse_dates=[],
                  ints_with_nan=['harvest_user_id'])

    print('PLACEHOLDERS')
    placeholders = response_to_df(api.get_placeholders(), title='PLACEHOLDERS')
    if data_store == 'csv':
        placeholders.to_csv('../data/forecast/placeholders.csv')
    else:
        df_to_sql(connection, 'forecast', 'placeholders', placeholders,
                  usecols=['name', 'archived'],
                  parse_dates=[],
                  ints_with_nan=[])

    print('MILESTONES')
    milestones = response_to_df(api.get_milestones(), title='MILESTONES')
    if data_store == 'csv':
        milestones.to_csv('../data/forecast/milestones.csv')
    else:
        df_to_sql(connection, 'forecast', 'milestones', milestones,
                  usecols=['date', 'project_id'],
                  parse_dates=['date'],
                  ints_with_nan=['project_id'])

    print('ASSIGNMENTS')
    assignments = response_to_df(api.get_assignments(), title='ASSIGNMENTS')
    if data_store == 'csv':
        assignments.to_csv('../data/forecast/assignments.csv')
    else:
        df_to_sql(connection, 'forecast', 'assignments', assignments,
                  usecols=['person_id', 'placeholder_id', 'project_id', 'start_date', 'end_date', 'allocation',
                           'notes'],
                  parse_dates=['start_date', 'end_date'],
                  ints_with_nan=['person_id', 'placeholder_id', 'project_id'])

    print('='*50)
    print('DONE! ({:.1f}s)'.format(time.time()-start))


def update_harvest(data_store='csv', connection=None):
    """
    Extract harvest data using the python-harvest package.

    NB: The master branch of python-harvest currently seems to be using the v1 version of the api. This version of the API
    is deprecated. The branch "v2_dev" of python-harvest works with harvests v2 API but doesn't seem to be fully functioning for
    all tables, most noticeably the time_entries table.
    """

    start = time.time()

    if data_store == 'csv':
        check_dir('../data/harvest')

    secrets = wimbledon.config.get_harvest_credentials()

    token = harvest.PersonalAccessToken(account_id=secrets.harvest_api_credentials['harvest_account_id'],
                                        access_token=secrets.harvest_api_credentials['access_token'])

    client = harvest.Harvest("https://api.harvestapp.com/api/v2", token)

    auth_user = client.get_currently_authenticated_user()

    print('AUTHENTICATED USER:')
    print(auth_user.first_name, auth_user.last_name, auth_user.email)

    def objs_to_df(objs, prefix=None,title=''):
        """Convert the attributes of each object in a list of objects into a pandas dataframe."""
        df = [obj.__dict__ for obj in objs]
        df = pd.DataFrame.from_dict(df)

        # add prefix to columns if given
        if prefix is not None:
            df.columns = prefix + '.' + df.columns

        # unpack any harvest objects into normal columns of values
        df = unpack_class_columns(df)

        return df

    def unpack_class_columns(df):
        """python-harvest returns some columns as an instance of another harvest data type.
        This function unpacks the values of those columns, creating a new column for each
        of the unpacked attributes (with name <COL_NAME>.<ATTRIBUTE_NAME>)"""

        # all columns which have ambiguous pandas 'object' type
        obj_cols = df.columns[df.dtypes == 'object']

        # most common type in each of these columns, excluding missing values
        col_types = {col: df[col].dropna().apply(type).mode() for col in obj_cols}

        # exclude columns which have no most common type (i.e. empty columns)
        col_types = {col: str(mode[0]) for col, mode in col_types.items() if len(mode) > 0}

        # find columns containing some instance from the harvest library
        harvest_cols = [col for col, mode in col_types.items() if 'harvest' in mode]

        # convert each column of harvest objects into a pandas df
        unpacked_cols = [objs_to_df(df[col], prefix=col) for col in harvest_cols]

        # add new columns to data frame
        for new_cols in unpacked_cols:
            df = pd.concat([df, new_cols], axis=1, sort=True)

        # remove original harvest object columns
        df.drop(harvest_cols, axis=1, inplace=True)

        return df

    def get_all_pages(client_function):
        """The harvest API returns max 100 results per query. This function calls the API as many times
        as necessary to extract all the query results.

        client_function: a function from an initiated python-harvest client, e.g. client.users"""

        result = client_function()
        total_pages = result.total_pages

        # the data to convert is in an attribute of the response, e.g. in a users response the data is in result.users
        df = objs_to_df(getattr(result, client_function.__name__))

        # get the remaining pages, if there are any
        if result.total_pages > 1:
            for i in range(2, total_pages + 1):
                result = client_function(page=i)
                result = objs_to_df(getattr(result, client_function.__name__))

                df = df.append(result, ignore_index=True)

        df.set_index('id', inplace=True)

        return df

    print('CLIENTS')
    clients = get_all_pages(client.clients)
    if data_store == 'csv':
        clients.to_csv('../data/harvest/clients.csv')
    else:
        df_to_sql(connection, 'harvest', 'clients', clients,
                  usecols=['name', 'is_active'],
                  parse_dates=[],
                  ints_with_nan=[])

    print('PROJECTS')
    projects = get_all_pages(client.projects)
    if data_store == 'csv':
        projects.to_csv('../data/harvest/projects.csv')
    else:
        df_to_sql(connection, 'harvest', 'projects', projects,
                  usecols=['name', 'budget', 'code', 'starts_on', 'ends_on', 'client.id', 'notes', 'is_active'],
                  parse_dates=['starts_on', 'ends_on'],
                  ints_with_nan=['client.id'])

    print('ROLES')
    roles = get_all_pages(client.roles)
    if data_store == 'csv':
        roles.to_csv('../data/harvest/roles.csv')
    else:
        df_to_sql(connection, 'harvest', 'roles', roles,
                  usecols=['name'],
                  parse_dates=[],
                  ints_with_nan=[])

    print('USERS')
    users = get_all_pages(client.users)
    if data_store == 'csv':
        users.to_csv('../data/harvest/users.csv')
    else:
        df_to_sql(connection, 'harvest', 'users', users,
                  usecols=['first_name', 'last_name', 'email', 'weekly_capacity', 'is_active',
                           'is_project_manager', 'is_contractor'],
                  parse_dates=[],
                  ints_with_nan=[])

    print('TASKS')
    tasks = get_all_pages(client.tasks)
    if data_store == 'csv':
        tasks.to_csv('../data/harvest/tasks.csv')
    else:
        df_to_sql(connection, 'harvest', 'tasks', tasks,
                  usecols=['name', 'is_active'],
                  parse_dates=[],
                  ints_with_nan=[])

    print('USER ASSIGNMENTS')
    user_assignments = get_all_pages(client.user_assignments)
    if data_store == 'csv':
        user_assignments.to_csv('../data/harvest/user_assignments.csv')
    else:
        df_to_sql(connection, 'harvest', 'user_assignments', user_assignments,
                  usecols=['user.id', 'project.id', 'is_active', 'is_project_manager'],
                  parse_dates=[],
                  ints_with_nan=['user.id', 'project.id'])

    print('TASK ASSIGNMENTS')
    task_assignments = get_all_pages(client.task_assignments)
    if data_store == 'csv':
        task_assignments.to_csv('../data/harvest/task_assignments.csv')
    else:
        df_to_sql(connection, 'harvest', 'task_assignments', task_assignments,
                  usecols=['task.id', 'project.id'],
                  parse_dates=[],
                  ints_with_nan=['task.id', 'project.id'])

    '''
    Issues with python-harvest modeule:
    
    time_entries: Currently fails due to time_entries.cost_rate should be "float" instead of "NoneType" error

    client_contacts, invoices, estimates, expenses: Also fail, usually due to some missing field error, but not sure we
    use any of those tables?

    Below is my own quick function to extract the time entries data... it's quite slow requiring 30+ queries, but the API
    returns max 100 results at a time so probably not a lot that can be done to improve it.
    '''

    def api_to_df(table, headers):
        """Query all pages of a table in harvest."""

        url = "https://api.harvestapp.com/v2/" + table
        print('Querying', url, '...', end='')

        req_time = time.time()
        response = requests.get(url, headers=headers)
        json_response = response.json()

        df = json_normalize(json_response[table])

        diff = time.time() - req_time
        print('{:.1f} seconds'.format(diff))

        while json_response['links']['next'] is not None:
            url = json_response['links']['next']
            print('Querying', url, '... ', end='')
            req_time = time.time()

            response = requests.get(url, headers=headers)
            json_response = response.json()

            new_entries = json_normalize(json_response[table])
            df = df.append(new_entries)

            diff = time.time() - req_time
            print('{:.1f} seconds'.format(diff))

            # wait a bit to prevent getting throttled (allowed max 100 requests per 15 seconds)
            if diff < 0.15:
                time.sleep(0.15 - diff)

        df.set_index('id', inplace=True)

        return df

    api_headers = {
        "User-Agent": "Hut23@turing.ac.uk",
        "Authorization": "Bearer " + secrets.harvest_api_credentials['access_token'],
        "Harvest-Account-ID": secrets.harvest_api_credentials['harvest_account_id']
    }

    print('TIME ENTRIES:')
    time_entries = api_to_df('time_entries', api_headers)
    if data_store == 'csv':
        time_entries.to_csv('../data/harvest/time_entries.csv')
    else:
        df_to_sql(connection, 'harvest', 'time_entries', time_entries,
                  usecols=['user.id', 'project.id', 'task.id', 'spent_date', 'hours', 'notes'],
                  parse_dates=['spent_date'],
                  ints_with_nan=['user.id', 'project.id', 'task.id'])

    print('='*50)
    print('DONE! ({:.1f}s)'.format(time.time()-start))


def update(run_harvest=True, run_forecast=True, data_store='csv'):
    if (data_store != 'csv') and (data_store != 'sql'):
        return ValueError('data_store must be csv or sql')

    if data_store == 'sql':
        connection = get_db_connection()
    else:
        connection = None

    if run_harvest:
        update_harvest(data_store=data_store, connection=connection)

    if run_forecast:
        update_forecast(data_store=data_store, connection=connection)
