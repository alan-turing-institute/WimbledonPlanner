"""
The functions in this script rely on the file secrets.py existing in the same directory and containing
authentication information for Harvest and Forecast as a dictionary with the following form:

harvest_api_credentials = {
    "harvest_account_id": "<HARVEST_ACCOUNT_ID>",
    "forecast_account_id": "<FORECAST_ACCOUNT_ID>",
    "access_token": "<ACCESS_TOKEN>"
"""
import secrets

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


def update_forecast():
    """
    Extract forecast data from its API using the pyforecast package.

    To install pyforecast, run:
    pip install pyforecast

    NB: The forecast API is not public and is undocumented. See:
    https://help.getharvest.com/forecast/faqs/faq-list/api/
    """
    start = time.time()

    check_dir('../data/forecast')

    api = forecast.Api(account_id=secrets.harvest_api_credentials['forecast_account_id'],
                       auth_token=secrets.harvest_api_credentials['access_token'])

    user = api.whoami()
    print()
    print('AUTHENTICATED USER:')
    print(user.first_name, user.last_name, user.email)
    print()

    def response_to_df(api_response, title=''):
        """Takes an api response in the pyforecast foremat and converts it into a pandas data frame."""
        results = [json.loads(result.to_json()) for result in api_response]

        df = json_normalize(results)
        df.set_index('id', inplace=True)

        return df

    print('PROJECTS')
    projects = response_to_df(api.get_projects(), title='PROJECTS')
    projects.to_csv('../data/forecast/projects.csv')

    print('PEOPLE')
    people = response_to_df(api.get_people(), title='PEOPLE')
    people.to_csv('../data/forecast/people.csv')

    print('CLIENTS')
    clients = response_to_df(api.get_clients(), title='CLIENTS')
    clients.to_csv('../data/forecast/clients.csv')

    print('ASSIGNMENTS')
    assignments = response_to_df(api.get_assignments(), title='ASSIGNMENTS')
    assignments.to_csv('../data/forecast/assignments.csv')

    print('MILESTONES')
    milestones = response_to_df(api.get_milestones(), title='MILESTONES')
    milestones.to_csv('../data/forecast/milestones.csv')

    print('ROLES')
    roles = response_to_df(api.get_roles(), title='ROLES')
    roles.to_csv('../data/forecast/roles.csv')

    print('CONNECTIONS')
    connections = response_to_df(api.get_user_connections(), title='CONNECTIONS')
    connections.to_csv('../data/forecast/connections.csv')

    print('PLACEHOLDERS')
    placeholders = response_to_df(api.get_placeholders(),title='PLACEHOLDERS')
    placeholders.to_csv('../data/forecast/placeholders.csv')

    print('='*50)
    print('DONE! ({:.1f}s)'.format(time.time()-start))


def update_harvest():
    """
    Extract harvest data using the python-harvest package.

    NB: The master branch of python-harvest currently seems to be using the v1 version of the api. This version of the API
    is deprecated. The branch "v2_dev" of python-harvest works with harvests v2 API but doesn't seem to be fully functioning for
    all tables, most noticeably the time_entries table.
    """

    start = time.time()

    check_dir('../data/harvest')

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

    print('USERS')
    users = get_all_pages(client.users)
    users.to_csv('../data/harvest/users.csv')

    print('PROJECTS')
    projects = get_all_pages(client.projects)
    projects.to_csv('../data/harvest/projects.csv')

    print('USER ASSIGNMENTS')
    user_assignments = get_all_pages(client.user_assignments)
    user_assignments.to_csv('../data/harvest/user_assignments.csv')

    print('TASK ASSIGNMENTS')
    task_assignments = get_all_pages(client.task_assignments)
    task_assignments.to_csv('../data/harvest/task_assignments.csv')

    print('TASKS')
    tasks = get_all_pages(client.tasks)
    tasks.to_csv('../data/harvest/tasks.csv')

    print('ROLES')
    roles = get_all_pages(client.roles)
    roles.to_csv('../data/harvest/roles.csv')

    print('CLIENTS')
    clients = get_all_pages(client.clients)
    clients.to_csv('../data/harvest/clients.csv')

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
    time_entries.to_csv('../data/harvest/time_entries.csv')

    print('='*50)
    print('DONE! ({:.1f}s)'.format(time.time()-start))
