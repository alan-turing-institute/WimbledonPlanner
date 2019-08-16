"""
Get latest data from Harvest & Forecast APIs and use it to
update our database.
"""
import wimbledon.sql.schema as schema
import wimbledon.sql.db_utils as db_utils
from wimbledon.harvest import api_interface

import sqlalchemy as sqla

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
        fc_to_hv_dict = hv.dropna().to_dict()

        # replace any missing harvest ids with the original
        # (forecast) ids
        ids[ids.isnull()] = fc_idx[ids.isnull()].values

    else:
        ids = df.index
        fc_to_hv_dict = None

    ids = prep_data(ids, int)

    return ids, fc_to_hv_dict


def merge_placeholders(placeholders,
                       names=['resource required', 'unconfirmed', 'deferred']):
    """consolidate names like Resource Required 1 into single placeholder
    RESOURCE REQUIRED"""
    
    # avoid overwriting original df
    placeholders = placeholders.copy(deep=True)
    # dictionary of {old key: new key} for merged keys
    merged_keys_dict = dict()
    for name in names:
        # find rows that contain a case insensitive match to name
        matches = placeholders[
                    placeholders['name'].str.lower().
                    str.contains(name.lower())
                  ].sort_values(by='name')

        # preserve the first match
        keep_idx = matches.index[0]
        # keys of remaining matches will be replaced with first one
        merged_keys_dict.update({idx: keep_idx for idx in matches.index[1:]})
        # change preserved name to upper case of input name
        placeholders.loc[keep_idx, 'name'] = name.upper()
        # drop other matches from df
        placeholders.drop(matches.index[1:], inplace=True)

    return placeholders, merged_keys_dict


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


def update_db(conn=None, with_tracked_time=True):
    if conn is None:
        conn = db_utils.get_db_connection()

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    print('=' * 50)
    print('HARVEST')
    print('=' * 50)
    hv = api_interface.get_harvest()

    # Client
    print('-' * 50)
    print('CLIENTS')
    print('-' * 50)

    client_hv_ids, _ = convert_index(hv['clients'])
    names = prep_data(hv['clients'].name, str)

    clients = [{'id': client_hv_ids[i],
                'name': names[i]}
               for i in range(len(client_hv_ids))]

    db_utils.upsert(schema.clients, clients, conn)

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

    db_utils.upsert(schema.people, people, conn)
    
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

    db_utils.upsert(schema.projects, projects, conn)
    
    if with_tracked_time:
        # Task
        print('-' * 50)
        print('TASKS')
        print('-' * 50)
        task_ids, _ = convert_index(hv['tasks'])
        names = prep_data(hv['tasks'].name, str)

        tasks = [dict(id=task_ids[i],
                    name=names[i])
                for i in range(len(task_ids))]

        db_utils.upsert(schema.tasks, tasks, conn)

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

        db_utils.upsert(schema.time_entries, time_entries, conn)
    
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Get Forecast data
    print('=' * 50)
    print('FORECAST')
    print('=' * 50)
    fc = api_interface.get_forecast()

    # Client
    print('-' * 50)
    print('CLIENTS')
    print('-' * 50)

    client_fc_ids, fc_to_hv_clients = convert_index(fc['clients'])
    names = prep_data(fc['clients'].name, str)

    clients = [{'id': client_fc_ids[i],
                'name': names[i]}
               for i in range(len(client_fc_ids))]

    db_utils.upsert(schema.clients, clients, conn)

    # Association
    print('-' * 50)
    print('ASSOCIATIONS')
    print('-' * 50)
    associations = [dict(id=idx, name=name)
                    for name, idx in association_groups.items()]

    db_utils.upsert(schema.associations, associations, conn)

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

    db_utils.upsert(schema.people, people, conn)

    # Placeholders
    print('-' * 50)
    print('PLACHEOLDERS')
    print('-' * 50)
    
    # consolidate placeholder names
    placeholders, merged_placeholders = merge_placeholders(fc['placeholders'])
    placeholder_ids, _ = convert_index(placeholders)
    names = prep_data(placeholders.name, str)
    associations = prep_data(placeholders.roles.apply(get_assoc_group),
                             int)

    placeholders = [dict(id=placeholder_ids[i],
                         name=names[i],
                         association=associations[i])
                    for i in range(len(placeholder_ids))]

    db_utils.upsert(schema.people, placeholders, conn)

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

    db_utils.upsert(schema.projects, projects, conn)

    # Assignment
    print('-' * 50)
    print('ASSIGNMENTS')
    print('-' * 50)

    # replace keys for previously merged placeholders
    fc['assignments']['placeholder_id'].replace(merged_placeholders,
                                                inplace=True)
                                     
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

    db_utils.upsert(schema.assignments, assignments, conn)

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    print('-' * 50)
    print('DELETIONS - Rows no longer in Harvest or Forecast')
    print('-' * 50)
    # Delete ids that are no longer in Forecast/Harvest
    # NB: ORDER IS IMPORTANT!! E.g. Must delete assignments to a project before
    # that project can be deleted.
    db_utils.delete_not_in(schema.assignments, assignment_ids, conn)

    if with_tracked_time:
        db_utils.delete_not_in(schema.time_entries, time_entry_ids, conn)
        db_utils.delete_not_in(schema.tasks, task_ids, conn)

    db_utils.delete_not_in(schema.projects,
                           project_fc_ids + project_hv_ids,
                           conn)

    db_utils.delete_not_in(schema.people,
                           placeholder_ids + people_fc_ids + people_hv_ids,
                           conn)

    db_utils.delete_not_in(schema.clients,
                           client_fc_ids + client_hv_ids,
                           conn)        

    conn.close()


if __name__ == '__main__':
    # disable SettingWithCopyWarning
    with pd.option_context('mode.chained_assignment', None):
        update_db()
