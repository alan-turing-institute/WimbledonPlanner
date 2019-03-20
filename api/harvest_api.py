"""
harvest_api.py
Extract harvest data using the python-harvest package.

The master branch of python-harvest currently seems to be using the v1 version of the api. This version of the API
is deprecated.

The branvh "v2_dev" of python-harvest works with harvests v2 API but doesn't seem to be fully functioning for
all tables, most noticeably the time_entries table.

To install the v2_dev branch of python-harvest for this script, run:
pip install git+https://github.com/lionheart/python-harvest@v2_dev
"""

import harvest
import config

import pandas as pd

token = harvest.PersonalAccessToken(account_id=config.harvest['account_id'],
                                    access_token=config.harvest['access_token'])

client = harvest.Harvest("https://api.harvestapp.com/api/v2", token)

auth_user = client.get_currently_authenticated_user()

print('AUTHENTICATED USER:')
print(auth_user.first_name, auth_user.last_name, auth_user.email)


def print_df(df, title=''):
    print()
    print('=' * 20 + title + '=' * 20)
    n_rows, n_columns = df.shape
    print('Number rows:', n_rows)
    print('Number columns:', n_columns)
    print('-' * 10 + 'Columns' + '-' * 10)
    print(df.columns.values)
    print('-' * 10 + 'First Row' + '-' * 10)
    print(df.iloc[0])


def objs_to_df(objs, prefix=None, verbose=False, title=''):
    """Convert the attributes of each object in a list of objects into a pandas dataframe."""
    df = [obj.__dict__ for obj in objs]
    df = pd.DataFrame.from_dict(df)

    # add prefix to columns if given
    if prefix is not None:
        df.columns = prefix + '.' + df.columns

    # unpack any harvest objects into normal columns of values
    df = unpack_class_columns(df)

    # print some info about the data frame
    if verbose:
        print_df(df, title=title)

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
    harvest_cols = [col for col,mode in col_types.items() if 'harvest' in mode]

    # convert each column of harvest objects into a pandas df
    unpacked_cols = [objs_to_df(df[col], prefix=col, verbose=False) for col in harvest_cols]

    # add new columns to data frame
    for new_cols in unpacked_cols:
        df = pd.concat([df, new_cols], axis=1, sort=True)

    # remove original harvest object columns
    df.drop(harvest_cols, axis=1, inplace=True)

    return df


def get_all_pages(client_function, verbose=True, title=''):
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

    if verbose:
        print_df(df, title=title)

    return df


users = get_all_pages(client.users, title='USERS')
users.to_csv('../data/harvest/users.csv')

projects = get_all_pages(client.projects, title='PROJECTS')
projects.to_csv('../data/harvest/projects.csv')

user_assignments = get_all_pages(client.user_assignments, title='USER ASSIGNMENTS')
user_assignments.to_csv('../data/harvest/user_assignments.csv')

task_assignments = get_all_pages(client.task_assignments, title='TASK ASSIGNMENTS')
task_assignments.to_csv('../data/harvest/task_assignments.csv')

tasks = get_all_pages(client.tasks, title='TASKS')
tasks.to_csv('../data/harvest/tasks.csv')

roles = get_all_pages(client.roles, title='ROLES')
roles.to_csv('../data/harvest/roles.csv')

'''
time_entries: Currently fails due to time_entries.cost_rate should be "float" instead of "NoneType" error

client_contacts, invoices, estimates, expenses: Also fail, usually due to some missing field error, but not sure we
use any of those tables?
'''
