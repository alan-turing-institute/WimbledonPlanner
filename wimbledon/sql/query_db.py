from wimbledon.sql import db_utils
import pandas as pd


def get_data(conn=None):
    """load data from a wimbledon database conn"""

    if conn is None:
        conn = db_utils.get_db_connection()

    data = dict()

    data['people'] = pd.read_sql_table('people', conn,
                                       index_col='id')

    data['clients'] = pd.read_sql_table('clients', conn,
                                        index_col='id')

    data['projects'] = pd.read_sql_table(
                            'projects', conn,
                            index_col='id',
                            parse_dates=['start_date', 'end_date']
                        )

    data['assignments'] = pd.read_sql_table(
                                'assignments', conn,
                                index_col='id',
                                parse_dates=['start_date', 'end_date']
                            )

    data['time_entries'] = pd.read_sql_table(
                                'time_entries', conn,
                                index_col='id',
                                parse_dates=['start_date', 'end_date']
                            )

    data['tasks'] = pd.read_sql_table('tasks', conn,
                                      index_col='id')

    data['associations'] = pd.read_sql_table('associations', conn,
                                             index_col='id')

    return data
