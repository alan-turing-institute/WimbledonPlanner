"""
forecast_api.py
Extract forecast data from its API using the pyforecast package.

To install pyforecast, run:
pip install pyforecast

NB: The forecast API is not public and is undocumented. See:
https://help.getharvest.com/forecast/faqs/faq-list/api/

The user id, token etc. is taken from the file config.py, which should be in the same directory as this script and
contain the following dictionary:
forecast = {'account_id': '<ACCOUNT_ID>',
            'auth_token': '<AUTH_TOKEN>'}

To get the account id and access token, set up a personal access token here:
https://id.getharvest.com/developers
You must choose the Turing Institute Forecast account in the token setup, not the Harvest account.
"""

import config
import forecast
import json
from pandas.io.json import json_normalize


api = forecast.Api(account_id=config.forecast['account_id'],
                   auth_token=config.forecast['auth_token'])

user = api.whoami()
print()
print('AUTHENTICATED USER:')
print(user.first_name, user.last_name, user.email)
print()


def print_df(df, title=''):
    """Print some information about a data frame."""
    print()
    print('=' * 20 + title + '=' * 20)
    n_rows, n_columns = df.shape
    print('Number rows:', n_rows)
    print('Number columns:', n_columns)
    print('-' * 10 + 'Columns' + '-' * 10)
    print(df.columns.values)
    print('-' * 10 + 'First Row' + '-' * 10)
    print(df.iloc[0])
    print()


def response_to_df(api_response, verbose=True, title=''):
    """Takes an api response in the pyforecast foremat and converts it into a pandas data frame."""
    results = [json.loads(result.to_json()) for result in api_response]

    df = json_normalize(results)
    df.set_index('id', inplace=True)

    if verbose:
        print_df(df, title=title)

    return df


projects = response_to_df(api.get_projects(), title='PROJECTS')
projects.to_csv('../data/forecast/projects.csv')

people = response_to_df(api.get_people(), title='PEOPLE')
people.to_csv('../data/forecast/people.csv')

clients = response_to_df(api.get_clients(), title='CLIENTS')
clients.to_csv('../data/forecast/clients.csv')

assignments = response_to_df(api.get_assignments(), title='ASSIGNMENTS')
assignments.to_csv('../data/forecast/assignments.csv')

milestones = response_to_df(api.get_milestones(), title='MILESTONES')
milestones.to_csv('../data/forecast/milestones.csv')

roles = response_to_df(api.get_roles(), title='ROLES')
roles.to_csv('../data/forecast/roles.csv')

connections = response_to_df(api.get_user_connections(), title='CONNECTIONS')
connections.to_csv('../data/forecast/connections.csv')
