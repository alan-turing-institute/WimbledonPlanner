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


def prep_data(series, typefn, convert_dict=None):
    """converts each element in series (a pandas series) using
    to_type_or_none with typefn.
    optionally change values in given series, e.g. to
    replace forecast ids with harvest ids.
    convert_dict is an {old_value:new_value dict}"""
    if convert_dict:
        series = series.replace(convert_dict)
        
    return list(map(lambda x: to_type_or_none(x, typefn), series.values))


def string_to_date(string, fmt='%Y-%m-%d'):
    return datetime.strptime(string, fmt).date()


def convert_index(df):
    """
    1. If a harvest_user_id column is present, use that instead
    of the original index.
    2. If harvest_user_id is not present, or missing/nan, use the
    original index value.
    3. Convert the indices to ints.
    """
    if 'harvest_user_id' in df.columns or 'harvest_id' in df.columns:
        # the original index -> generally forecast ids
        fc_idx = df.index

        if 'harvest_user_id' in df.columns:
            hv = df['harvest_user_id']
        else:
            hv = df['harvest_id']

        # the desired index -> the harvest ids
        ids = hv
        # also keep a dictionary that can be used to convert
        # between forecast and harvest ids
        fc_to_hv_dict = hv.to_dict()

        # replace any missing harvest ids with the original
        # (forecast) ids
        ids[ids.isnull()] = fc_idx[ids.isnull()].values

    else:
        ids = df.index
        fc_to_hv_dict = None

    ids = prep_data(ids, int)

    return ids, fc_to_hv_dict


def combine_people_placeholders(people, placeholders):
    """replace all null values in people (pandas series)
    with value from placeholders. E.g. to get one column
    of ids for assignments.
    people and placeholders should share same index, i.e.
    columns from same dataframe."""

    people[people.isnull()] = placeholders[people.isnull()].values

    return people


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


def make_upsert(table, data, conn,
                index_elements=['id'], exclude_columns=['id']):
    """
    table: sqlalchemy table ojbect
    data: list of {colname: value} dicts
    conn: db connection to execute upsert on
    index_elements: index columns to check for conflicts on
    exclude_columns: don't update these columns
    """
    print('First row in data:', data[0])

    insert_stmt = psql_insert(table).values(data)

    update_columns = {col.name: col for col in insert_stmt.excluded
                      if col.name not in exclude_columns}

    upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=index_elements,
                    set_=update_columns)

    r = conn.execute(upsert_stmt)
    
    print(r.rowcount, 'rows added/updated in', table.name)


def delete_not_in_harvest(table, ids, conn):
    """
    delete ids in our database that are not present in the
    harvest/forecast database.
    """
    delete_stmt = table.delete().where(table.c.id.notin_(ids))
    r = conn.execute(delete_stmt)
    print(r.rowcount, 'rows deleted from', table.name)


def update_db(driver, host, db):
    engine = sqla.create_engine(driver + '://' + host + '/' + db)
    conn = engine.connect()

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    print('=' * 50)
    print('HARVEST')
    print('=' * 50)
    hv = DataUpdater.get_harvest()

    # Client
    print('-' * 50)
    print('CLIENTS')
    print('-' * 50)

    client_hv_ids, _ = convert_index(hv['clients'])
    names = prep_data(hv['clients'].name, str)

    clients = [{'id': client_hv_ids[i],
                'name': names[i]}
               for i in range(len(client_hv_ids))]

    make_upsert(schema.clients, clients, conn)

    # Person
    print('-' * 50)
    print('PEOPLE')
    print('-' * 50)

    people_hv_ids, fc_to_hv_people = convert_index(hv['users'])
    names = prep_data(hv['users'].first_name + ' ' +
                      hv['users'].last_name, str)

    people = [dict(id=people_hv_ids[i],
                   name=names[i])
              for i in range(len(people_hv_ids))]

    make_upsert(schema.people, people, conn)
    
    # Project
    print('-' * 50)
    print('PROJECTS')
    print('-' * 50)

    project_hv_ids, _ = convert_index(hv['projects'])
    names = prep_data(hv['projects'].name, str)
    # NB: convert forecast client idx to harvest idx
    clients = prep_data(hv['projects']['client.id'], int)
    start_dates = prep_data(hv['projects']['starts_on'], string_to_date)
    end_dates = prep_data(hv['projects']['ends_on'], string_to_date)
    
    projects = [dict(id=project_hv_ids[i],
                     name=names[i],
                     client=clients[i],
                     start_date=start_dates[i],
                     end_date=end_dates[i])
                for i in range(len(project_hv_ids))]

    make_upsert(schema.projects, projects, conn)
    
    # Task
    print('-' * 50)
    print('TASKS')
    print('-' * 50)
    task_ids, _ = convert_index(hv['tasks'])
    names = prep_data(hv['tasks'].name, str)

    tasks = [dict(id=task_ids[i],
                  name=names[i])
             for i in range(len(task_ids))]

    make_upsert(schema.tasks, tasks, conn)

    # TimeEntry
    print('-' * 50)
    print('TIME ENTRIES')
    print('-' * 50)
    time_entry_ids, _ = convert_index(hv['time_entries'])
    projects = prep_data(hv['time_entries']['project.id'], int)
    people = prep_data(hv['time_entries']['user.id'], int)
    tasks = prep_data(hv['time_entries']['task.id'], int)
    dates = prep_data(hv['time_entries']['spent_date'], string_to_date)
    hours = prep_data(hv['time_entries']['hours'], int)

    time_entries = [dict(id=time_entry_ids[i],
                         project=projects[i],
                         person=people[i],
                         task=tasks[i],
                         date=dates[i],
                         hours=hours[i])
                    for i in range(len(time_entry_ids))]

    make_upsert(schema.time_entries, time_entries, conn)
    
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Get Forecast data
    print('=' * 50)
    print('FORECAST')
    print('=' * 50)
    fc = DataUpdater.get_forecast()

    # Client
    print('-' * 50)
    print('CLIENTS')
    print('-' * 50)

    client_fc_ids, fc_to_hv_clients = convert_index(fc['clients'])
    names = prep_data(fc['clients'].name, str)

    clients = [{'id': client_fc_ids[i],
                'name': names[i]}
               for i in range(len(client_fc_ids))]

    make_upsert(schema.clients, clients, conn)

    # Association
    print('-' * 50)
    print('ASSOCIATIONS')
    print('-' * 50)
    associations = [dict(id=idx, name=name)
                    for name, idx in association_groups.items()]

    make_upsert(schema.associations, associations, conn)

    # Person
    print('-' * 50)
    print('PEOPLE')
    print('-' * 50)

    people_fc_ids, fc_to_hv_people = convert_index(fc['people'])
    names = prep_data(fc['people'].first_name + ' ' +
                      fc['people'].last_name, str)

    associations = prep_data(fc['people'].roles.apply(get_assoc_group), int)

    people = [dict(id=people_fc_ids[i],
                   name=names[i],
                   association=associations[i])
              for i in range(len(people_fc_ids))]

    make_upsert(schema.people, people, conn)

    # Placeholders
    print('-' * 50)
    print('PLACHEOLDERS')
    print('-' * 50)

    placeholder_ids, _ = convert_index(fc['placeholders'])
    names = prep_data(fc['placeholders'].name, str)
    associations = prep_data(fc['placeholders'].roles.apply(get_assoc_group),
                             int)

    placeholders = [dict(id=placeholder_ids[i],
                         name=names[i],
                         association=associations[i])
                    for i in range(len(placeholder_ids))]

    make_upsert(schema.people, placeholders, conn)

    # Project
    print('-' * 50)
    print('PROJECTS')
    print('-' * 50)

    project_fc_ids, fc_to_hv_projects = convert_index(fc['projects'])
    names = prep_data(fc['projects'].name, str)
    # NB: convert forecast client idx to harvest idx
    clients = prep_data(fc['projects'].client_id, int,
                        convert_dict=fc_to_hv_clients)
    start_dates = prep_data(fc['projects'].start_date, string_to_date)
    end_dates = prep_data(fc['projects'].end_date, string_to_date)

    githubs = []
    for string in fc['projects'].tags:
        tags = re.findall(r"(?<=\'GitHub:)(.*?)(?=[\'\,])", str(string))

        if len(tags) > 0:
            githubs.append(int(tags[0]))
        else:
            githubs.append(None)

    projects = [dict(id=project_fc_ids[i],
                     name=names[i],
                     client=clients[i],
                     start_date=start_dates[i],
                     end_date=end_dates[i],
                     github=githubs[i])
                for i in range(len(project_fc_ids))]

    make_upsert(schema.projects, projects, conn)

    # Assignment
    print('-' * 50)
    print('ASSIGNMENTS')
    print('-' * 50)

    assignment_ids, _ = convert_index(fc['assignments'])
    # NB: convert forecast project idx to harvest idx
    projects = prep_data(fc['assignments'].project_id, int,
                         convert_dict=fc_to_hv_projects)
    # NB: combine people and placeholder ids
    # and convert forecast person idx to harvest idx
    people = combine_people_placeholders(fc['assignments'].person_id,
                                         fc['assignments'].placeholder_id)
    people = prep_data(people, int, convert_dict=fc_to_hv_people)

    start_dates = prep_data(fc['assignments'].start_date, string_to_date)
    end_dates = prep_data(fc['assignments'].end_date, string_to_date)
    allocations = prep_data(fc['assignments'].allocation, int)

    assignments = [dict(id=assignment_ids[i],
                        project=projects[i],
                        person=people[i],
                        start_date=start_dates[i],
                        end_date=end_dates[i],
                        allocation=allocations[i])
                   for i in range(len(assignment_ids))]

    make_upsert(schema.assignments, assignments, conn)

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    print('-' * 50)
    print('DELETIONS - Rows no longer in Harvest/Forecast')
    print('-' * 50)
    # Delete ids that are no longer in Forecast/Harvest
    # NB: ORDER IS IMPORTANT!! E.g. Must delete assignments to a project before
    # that project can be deleted.
    delete_not_in_harvest(schema.assignments, assignment_ids, conn)

    delete_not_in_harvest(schema.time_entries, time_entry_ids, conn)

    delete_not_in_harvest(schema.projects,
                          project_fc_ids + project_hv_ids,
                          conn)

    delete_not_in_harvest(schema.people,
                          placeholder_ids + people_fc_ids + people_hv_ids,
                          conn)

    delete_not_in_harvest(schema.clients,
                          client_fc_ids + client_hv_ids,
                          conn)
    
    delete_not_in_harvest(schema.tasks, task_ids, conn)

    conn.close()


if __name__ == '__main__':
    # Database setup
    driver = 'postgresql'
    host = 'localhost'
    db = 'wimbledon'

    # disable SettingWithCopyWarning
    with pd.option_context('mode.chained_assignment', None):
        update_db(driver, host, db)
