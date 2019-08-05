import wimbledon.api.sql.schema as schema
from wimbledon.api import DataUpdater

import sqlalchemy as sqla
from sqlalchemy.dialects.postgresql import insert as psql_insert

import re
import pandas as pd
import numpy as np
from datetime import datetime


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


def prep_data(series, typefn):
    """converts each element in series (a pandas series) using
    to_type_or_none with typefn"""
    return list(map(lambda x: to_type_or_none(x, typefn), series.values))


def string_to_date(string, fmt='%Y-%m-%d'):
    return datetime.strptime(string, fmt).date()


def make_upsert(table, data, index_elements=['id'], exclude_columns=['id']):
    """
    table: sqlalchemy table ojbect
    data: list of {colname: value} dicts
    index_elements: index columns to check for conflicts on
    exclude_columns: don't update these columns
    """

    insert_stmt = psql_insert(table).values(data)

    update_columns = {col.name: col for col in insert_stmt.excluded
                      if col.name not in exclude_columns}

    upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=index_elements,
                    set_=update_columns)

    return upsert_stmt


association_groups = {'Placeholder': 0,
                      'REG Director': 1,
                      'REG Principal': 2,
                      'REG Senior': 3,
                      'REG Permanent': 4,
                      'REG FTC': 5,
                      'REG Associate': 6,
                      'University Partner': 7}


def get_assoc_group(role_str):
    for group, index in association_groups.items():
        if group in role_str:
            return index

    return association_groups['Placeholder']


if __name__ == '__main__':
    # Database setup
    driver = 'postgresql'
    host = 'localhost'
    db = 'wimbledon'

    engine = sqla.create_engine(driver + '://' + host + '/' + db)
    conn = engine.connect()

    # Get Forecast data
    print('=' * 50)
    print('FORECAST')
    print('=' * 50)
    fc = DataUpdater.get_forecast()

    # Client
    print('-' * 50)
    print('CLIENTS')
    print('-' * 50)

    ids = prep_data(fc['clients'].index, int)
    names = prep_data(fc['clients'].name, str)

    clients = [{'id': ids[i],
                'name': names[i]}
               for i in range(len(ids))]

    upsert_stmt = make_upsert(schema.clients, clients)
    conn.execute(upsert_stmt)

    print(clients)

    # Association
    print('-' * 50)
    print('ASSOCIATIONS')
    print('-' * 50)
    associations = [dict(id=idx, name=name)
                    for name, idx in association_groups.items()]

    upsert_stmt = make_upsert(schema.associations, associations)
    conn.execute(upsert_stmt)

    print(associations)

    # Person
    print('-' * 50)
    print('PEOPLE')
    print('-' * 50)

    ids = prep_data(fc['people'].index, int)

    names = prep_data(fc['people'].first_name + ' ' +
                      fc['people'].last_name, str)

    associations = prep_data(fc['people'].roles.apply(get_assoc_group), int)

    people = [dict(id=ids[i],
                   name=names[i],
                   association=associations[i])
              for i in range(len(ids))]

    upsert_stmt = make_upsert(schema.people, people)
    conn.execute(upsert_stmt)

    print(people)

    # Placeholders
    print('-' * 50)
    print('PLACHEOLDERS')
    print('-' * 50)

    ids = prep_data(fc['placeholders'].index, int)
    names = prep_data(fc['placeholders'].name, str)
    associations = prep_data(fc['placeholders'].roles.apply(get_assoc_group),
                             int)

    placeholders = [dict(id=ids[i],
                         name=names[i],
                         association=associations[i])
                    for i in range(len(ids))]

    upsert_stmt = make_upsert(schema.people, placeholders)
    conn.execute(upsert_stmt)
    
    print(placeholders)

    # Project
    print('-' * 50)
    print('PROJECTS')
    print('-' * 50)

    ids = prep_data(fc['projects'].index, int)
    names = prep_data(fc['projects'].name, str)
    clients = prep_data(fc['projects'].client_id, int)
    start_dates = prep_data(fc['projects'].start_date, string_to_date)
    end_dates = prep_data(fc['projects'].end_date, string_to_date)

    githubs = []
    for string in fc['projects'].tags:
        tags = re.findall(r"(?<=\'GitHub:)(.*?)(?=[\'\,])", str(string))

        if len(tags) > 0:
            githubs.append(int(tags[0]))
        else:
            githubs.append(None)

    projects = [dict(id=ids[i],
                     name=names[i],
                     client=clients[i],
                     start_date=start_dates[i],
                     end_date=end_dates[i],
                     github=githubs[i])
                for i in range(len(ids))]

    upsert_stmt = make_upsert(schema.projects, projects)
    conn.execute(upsert_stmt)

    print(projects)

    # Assignment
    print('-' * 50)
    print('ASSIGNMENTS')
    print('-' * 50)

    ids = prep_data(fc['assignments'].index, int)
    projects = prep_data(fc['assignments'].project_id, int)
    people = prep_data(fc['assignments'].person_id, int)
    start_dates = prep_data(fc['assignments'].start_date, string_to_date)
    end_dates = prep_data(fc['assignments'].end_date, string_to_date)
    allocations = prep_data(fc['assignments'].allocation, int)

    assignments = [dict(id=ids[i],
                        project=projects[i],
                        person=people[i],
                        start_date=start_dates[i],
                        end_date=end_dates[i],
                        allocation=allocations[i])
                   for i in range(len(ids))]

    upsert_stmt = make_upsert(schema.assignments, assignments)
    conn.execute(upsert_stmt)

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
    
    conn.close()
