"""
Insert data from csv files into the database defined by config.json.
Runs once - subsequent runs will not update (delete and recreate database first)
"""
import sqlalchemy as sqla
import sys
import pandas as pd

import wimbledon.config


# function to load csv and insert it to database
def csv_to_sql(file_path, schema, table_name, usecols, parse_dates,
               ints_with_nan, index_col='id'):
    csv = pd.read_csv(file_path,
                      usecols=usecols,
                      index_col=index_col,
                      parse_dates=parse_dates,
                      infer_datetime_format=True)
    """
    Function to load csv and insert it to database.
    
    schema: forecast or harvest
    
    table_name: name of csv file and of corresponding table in database
    
    usecols: which columns from csv to send to database
    
    parse_dates: which columns in usecols are dates
    
    ints_with_nan: which columns in usecols are integers but may be interpreted
    as floats due to missing values
    
    index_col: which column is the index
    """

    print('='*50)
    print(schema+'.'+table_name)
    print('='*50)

    for col in ints_with_nan:
        # Integer columns with NaN: Requires pandas 0.24 (otherwise ids end up as floats)
        csv[col] = csv[col].astype('Int64')

    csv.columns = csv.columns.str.replace('.', '_')

    metadata = sqla.MetaData(schema=schema)

    csv.to_sql(table_name, connection, schema=schema, if_exists='append')
    table = sqla.Table(table_name, metadata, autoload=True, autoload_with=engine)
    results = connection.execute(sqla.select([table])).fetchall()
    df = pd.DataFrame(results)
    df.columns = results[0].keys()

    print(repr(metadata.tables[schema + '.' + table_name]))
    print(df.head())


# Update Harvest Tables
def update_harvest(data_dir):
    csv_to_sql(data_dir+'/clients.csv',
               'harvest', 'clients',
               usecols=['id', 'name', 'is_active'],
               parse_dates=False,
               ints_with_nan=[],
               index_col='id')

    csv_to_sql(data_dir+'/projects.csv',
               'harvest', 'projects',
               usecols=['id', 'name', 'budget', 'code', 'starts_on', 'ends_on', 'client.id', 'notes', 'is_active'],
               parse_dates=['starts_on', 'ends_on'],
               ints_with_nan=['client.id'],
               index_col='id')

    csv_to_sql(data_dir+'/roles.csv',
               'harvest', 'roles',
               usecols=['id', 'name'],
               parse_dates=False,
               ints_with_nan=[],
               index_col='id')

    csv_to_sql(data_dir+'/users.csv',
               'harvest', 'users',
               usecols=['id', 'first_name', 'last_name', 'email', 'roles', 'weekly_capacity', 'is_active', 'is_project_manager', 'is_contractor'],
               parse_dates=False,
               ints_with_nan=[],
               index_col='id')

    csv_to_sql(data_dir+'/tasks.csv',
               'harvest', 'tasks',
               usecols=['id', 'name', 'is_active'],
               parse_dates=False,
               ints_with_nan=[],
               index_col='id')

    csv_to_sql(data_dir+'/time_entries.csv',
               'harvest', 'time_entries',
               usecols=['id', 'user.id', 'project.id', 'task.id', 'spent_date', 'hours', 'notes'],
               parse_dates=['spent_date'],
               ints_with_nan=['user.id','project.id','task.id'],
               index_col='id')

    csv_to_sql(data_dir+'/user_assignments.csv',
               'harvest', 'user_assignments',
               usecols=['id', 'user.id', 'project.id', 'is_active', 'is_project_manager'],
               parse_dates=False,
               ints_with_nan=['user.id','project.id'],
               index_col='id')

    csv_to_sql(data_dir+'/task_assignments.csv',
               'harvest', 'task_assignments',
               usecols=['id', 'task.id', 'project.id'],
               parse_dates=False,
               ints_with_nan=['task.id','project.id'],
               index_col='id')


# Update Forecast Tables
def update_forecast(data_dir):
    csv_to_sql(data_dir+'/clients.csv',
               'forecast', 'clients',
               usecols=['id', 'name', 'harvest_id', 'archived'],
               parse_dates=False,
               ints_with_nan=['harvest_id'],
               index_col='id')

    csv_to_sql(data_dir+'/projects.csv',
               'forecast', 'projects',
               usecols=['id', 'name', 'code', 'start_date', 'end_date', 'client_id', 'harvest_id', 'notes', 'archived'],
               parse_dates=['start_date', 'end_date'],
               ints_with_nan=['client_id','harvest_id'],
               index_col='id')

    csv_to_sql(data_dir+'/roles.csv',
               'forecast', 'roles',
               usecols=['id', 'name', 'harvest_role_id'],
               parse_dates=False,
               ints_with_nan=['harvest_role_id'],
               index_col='id')

    csv_to_sql(data_dir+'/people.csv',
               'forecast', 'people',
               usecols=['id', 'first_name', 'last_name', 'email', 'roles', 'harvest_user_id', 'login', 'subscribed', 'admin',
                        'archived', 'weekly_capacity', 'working_days.monday', 'working_days.tuesday', 'working_days.wednesday',
                        'working_days.thursday', 'working_days.friday', 'working_days.saturday', 'working_days.sunday'],
               parse_dates=False,
               ints_with_nan=['harvest_user_id'],
               index_col='id')

    csv_to_sql(data_dir+'/placeholders.csv',
               'forecast', 'placeholders',
               usecols=['id', 'name', 'roles', 'archived'],
               parse_dates=False,
               ints_with_nan=[],
               index_col='id')

    csv_to_sql(data_dir+'/milestones.csv',
               'forecast', 'milestones',
               usecols=['id', 'date', 'project_id'],
               parse_dates=['date'],
               ints_with_nan=['project_id'],
               index_col='id')

    csv_to_sql(data_dir+'/assignments.csv',
               'forecast', 'assignments',
               usecols=['id', 'person_id', 'placeholder_id', 'project_id', 'start_date','end_date','allocation','notes'],
               parse_dates=['start_date','end_date'],
               ints_with_nan=['person_id','placeholder_id','project_id'],
               index_col='id')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        raise NameError("update_db.py must be passed a path to a data directory")

    config = wimbledon.config.get_sql_config()

    if config['host'] == 'localhost':
        url = sqla.engine.url.URL(drivername=config['drivername'],
                                  host=config['host'],
                                  database=config['database'])
    else:
        url = sqla.engine.url.URL(drivername=config['drivername'],
                                  username=config['username'],
                                  password=config['password'],
                                  host=config['host'],
                                  database=config['database'])

    engine = sqla.create_engine(url)
    connection = engine.connect()

    update_harvest(data_dir+'/harvest')
    update_forecast(data_dir+'/forecast')

