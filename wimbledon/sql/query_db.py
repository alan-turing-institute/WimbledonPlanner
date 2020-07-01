from wimbledon.sql import db_utils
import pandas as pd


def get_data(conn=None, with_tracked_time=True):
    """Extract wimbledon data from the database as pandas dataframes.

    Keyword Arguments:
        conn {sqlalchemy.engine.Connection} -- Connection to a wimbledon
        database. If none get from wimbledon config (default: {None})

        with_tracked_time {bool} -- whether to get time entries data (Harvest
        equivalents). Set to False for speed if not needed (default: {True})

    Returns:
        dict -- dictionary of pandas dataframes
    """

    if conn is None:
        conn = db_utils.get_db_connection()

    data = dict()

    data["people"] = pd.read_sql_table("people", conn, index_col="id")

    data["associations"] = pd.read_sql_table("associations", conn, index_col="id")

    data["clients"] = pd.read_sql_table("clients", conn, index_col="id")

    data["projects"] = pd.read_sql_table(
        "projects", conn, index_col="id", parse_dates=["start_date", "end_date"]
    )

    data["assignments"] = pd.read_sql_table(
        "assignments", conn, index_col="id", parse_dates=["start_date", "end_date"]
    )

    if with_tracked_time:
        data["time_entries"] = pd.read_sql_table(
            "time_entries", conn, index_col="id", parse_dates=["date"]
        )

        data["tasks"] = pd.read_sql_table("tasks", conn, index_col="id")

    return data
