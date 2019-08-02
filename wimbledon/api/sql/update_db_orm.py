import wimbledon.api.sql.schema as schema
from wimbledon.api import DataUpdater

import sqlalchemy as sqla
import sqlalchemy.orm as orm

import re
import pandas as pd
import numpy as np
from datetime import datetime

# Database setup
driver = 'postgresql'
host = 'localhost'
db = 'wimbledon'

engine = sqla.create_engine(driver + '://' + host + '/' + db)
schema.Base.metadata.create_all(engine)

Session = orm.sessionmaker(bind=engine)
session = Session()


def to_type_or_none(value, typefn):
    """performs typefn(value) if possible, else
    returns None.
    Warning: if value is float and typefn is int,
    will get floor(value) back!
    """
    try:
        return typefn(value)
    except:
        return None


def string_to_date(string, fmt='%Y-%m-%d'):
    return datetime.strptime(string, fmt).date()

# Get Forecast data
print('=' * 50)
print('FORECAST')
print('=' * 50)
fc = DataUpdater.get_forecast()

# Client
print('-' * 50)
print('CLIENTS')
print('-' * 50)

ids = fc['clients'].index.values
ids = list(map(lambda x: to_type_or_none(x, int), ids))

names = fc['clients'].name.values
names = list(map(lambda x: to_type_or_none(x, str), names))

clients = [schema.Client(id=ids[i], name=names[i]) for i in range(len(ids))]

session.add_all(clients)
session.commit()

print(clients)

# Association
print('-' * 50)
print('ASSOCIATIONS')
print('-' * 50)
association_groups = {'Placeholder': 0,
                      'REG Director': 1,
                      'REG Principal': 2,
                      'REG Senior': 3,
                      'REG Permanent': 4,
                      'REG FTC': 5,
                      'REG Associate': 6,
                      'University Partner': 7}

associations = [schema.Association(id=idx, name=name)
                for name, idx in association_groups.items()]

session.add_all(associations)
session.commit()

print(associations)

# Person
print('-' * 50)
print('PEOPLE')
print('-' * 50)

ids = fc['people'].index.values
ids = list(map(lambda x: to_type_or_none(x, int), ids))

names = (fc['people']['first_name'].values +
         ' ' +
         fc['people']['last_name'].values)
names = list(map(lambda x: to_type_or_none(x, str), names))


def get_assoc_group(role_str):
    for group, index in association_groups.items():
        if group in role_str:
            return index

    return association_groups['Placeholder']

associations = fc['people']['roles'].apply(get_assoc_group).values
associations = list(map(lambda x: to_type_or_none(x, int), associations))

people = [schema.Person(id=ids[i], name=names[i], association=associations[i])
          for i in range(len(ids))]

session.add_all(people)
session.commit()

print(people)

# Placeholders
print('-' * 50)
print('PLACHEOLDERS')
print('-' * 50)

ids = fc['placeholders'].index.values
ids = list(map(lambda x: to_type_or_none(x, int), ids))

names = fc['placeholders'].name.values
names = list(map(lambda x: to_type_or_none(x, str), names))

associations = fc['placeholders']['roles'].apply(get_assoc_group).values
associations = list(map(lambda x: to_type_or_none(x, int), associations))

placeholders = [schema.Person(id=ids[i],
                              name=names[i],
                              association=associations[i])
                for i in range(len(ids))]

session.add_all(placeholders)
session.commit()

print(placeholders)

# Project
print('-' * 50)
print('PROJECTS')
print('-' * 50)

ids = fc['projects'].index.values
ids = list(map(lambda x: to_type_or_none(x, int), ids))

names = fc['projects'].name.values
names = list(map(lambda x: to_type_or_none(x, str), names))

clients = fc['projects'].client_id.values
clients = list(map(lambda x: to_type_or_none(x, int), clients))

start_dates = fc['projects'].start_date
start_dates = list(map(lambda x: to_type_or_none(x, string_to_date),
                       start_dates))

end_dates = fc['projects'].end_date
end_dates = list(map(lambda x: to_type_or_none(x, string_to_date),
                     end_dates))

githubs = []
for string in fc['projects'].tags:
    tags = re.findall(r"(?<=\'GitHub:)(.*?)(?=[\'\,])", str(string))

    if len(tags) > 0:
        githubs.append(int(tags[0]))
    else:
        githubs.append(np.nan)

githubs = list(map(lambda x: to_type_or_none(x, int), githubs))

projects = [schema.Project(id=ids[i],
                           name=names[i],
                           client=clients[i],
                           start_date=start_dates[i],
                           end_date=end_dates[i],
                           github=githubs[i])
            for i in range(len(ids))]

session.add_all(projects)
session.commit()

print(projects)

# Assignment
print('-' * 50)
print('ASSIGNMENTS')
print('-' * 50)

ids = fc['assignments'].index.values
ids = list(map(lambda x: to_type_or_none(x, int), ids))

projects = fc['assignments'].project_id.values
projects = list(map(lambda x: to_type_or_none(x, int), projects))

people = fc['assignments'].person_id.values
people = list(map(lambda x: to_type_or_none(x, int), people))

start_dates = fc['assignments'].start_date
start_dates = list(map(lambda x: to_type_or_none(x, string_to_date),
                       start_dates))

end_dates = fc['assignments'].end_date
end_dates = list(map(lambda x: to_type_or_none(x, string_to_date),
                     end_dates))

allocations = fc['assignments'].allocation.values
allocations = list(map(lambda x: to_type_or_none(x, int), allocations))

assignments = [schema.Assignment(id=ids[i],
                                 project=projects[i],
                                 person=people[i],
                                 start_date=start_dates[i],
                                 end_date=end_dates[i],
                                 allocation=allocations[i])
               for i in range(len(ids))]

session.add_all(assignments)
session.commit()

print(assignments)

"""
print('=' * 50)
print('HARVEST')
print('=' * 50)
hv = DataUpdater.get_harvest()

# Task
print('-' * 50)
print('TASKS')
print('-' * 50)
ids = hv['tasks'].index.values
names = hv['tasks'].name.values
tasks = [schema.Task(id=ids[i], name=names[i]) for i in range(len(ids))]
print(tasks)

# TimeEntry
"""
