import forecast

import json

import pandas as pd
from pandas.io.json import json_normalize

import config

api = forecast.Api(account_id=config.forecast['account_id'],
                   auth_token=config.forecast['auth_token'])

projects = api.get_projects()
projects = [json.loads(proj.to_json()) for proj in projects]
projects = json_normalize(projects)
projects.set_index('id',inplace=True)
projects.to_csv('../data/forecast/projects.csv')

people = api.get_people()
people = [json.loads(pers.to_json()) for pers in people]
people = json_normalize(people)
people.set_index('id',inplace=True)
people.to_csv('../data/forecast/people.csv')

clients = api.get_clients()
clients = [json.loads(cli.to_json()) for cli in clients]
clients = json_normalize(clients)
clients.set_index('id',inplace=True)
clients.to_csv('../data/forecast/clients.csv')

assignments = api.get_assignments()
assignments = [json.loads(ass.to_json()) for ass in assignments]
assignments = json_normalize(assignments)
assignments.set_index('id',inplace=True)
# include person and project names in assignments table
assignments = pd.merge(assignments, people[['first_name','last_name']],
                       left_on='person_id',right_index=True,how='left')

assignments['person_name'] = assignments['first_name'] + ' ' + assignments['last_name']
assignments.drop(['first_name','last_name'],axis=1,inplace=True)

assignments = pd.merge(assignments, projects[['name']],
                       left_on='project_id',right_index=True,how='left')

assignments.rename(columns={'name':'project_name'},inplace=True)
#
assignments.to_csv('../data/forecast/assignments.csv')

milestones = api.get_milestones()
milestones = [json.loads(mile.to_json()) for mile in milestones]
milestones = json_normalize(milestones)
milestones.set_index('id',inplace=True)
milestones.to_csv('../data/forecast/milestones.csv')

roles = api.get_roles()
roles = [json.loads(rol.to_json()) for rol in roles]
roles = json_normalize(roles)
roles.set_index('id',inplace=True)
roles.to_csv('../data/forecast/roles.csv')

connections = api.get_user_connections()
connections = [json.loads(con.to_json()) for con in connections]
connections = json_normalize(connections)
connections.set_index('id',inplace=True)
connections.to_csv('../data/forecast/connections.csv')
