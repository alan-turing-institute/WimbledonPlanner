import sqlalchemy as sqla
from sqlalchemy.dialects.postgresql import insert as psql_insert

import wimbledon.config


def get_db_connection():
    engine = get_db_engine()
    conn = engine.connect()
    return conn


def get_db_engine():
    db_config = wimbledon.config.get_sql_config()
    url = sqla.engine.url.URL(
        drivername=db_config["drivername"],
        username=db_config["username"],
        password=db_config["password"],
        host=db_config["host"],
        port=db_config["port"],
        database=db_config["database"],
    )
    engine = sqla.create_engine(url)

    return engine


def upsert(table, data, conn, index_elements=["id"], exclude_columns=["id"]):
    """
    table: sqlalchemy table ojbect
    data: list of {colname: value} dicts
    conn: db connection to execute upsert on
    index_elements: index columns to check for conflicts on
    exclude_columns: don't update these columns
    """
    print("First row in data:", data[0])

    insert_stmt = psql_insert(table).values(data)

    update_columns = {
        col.name: col for col in insert_stmt.excluded if col.name not in exclude_columns
    }

    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=index_elements, set_=update_columns
    )

    r = conn.execute(upsert_stmt)

    print(r.rowcount, "rows added/updated in", table.name)


def delete_not_in(table, ids, conn):
    """
    delete rows in table that have an id which is not
    present in ids.
    """
    delete_stmt = table.delete().where(table.c.id.notin_(ids))
    r = conn.execute(delete_stmt)
    print(r.rowcount, "rows deleted from", table.name)
