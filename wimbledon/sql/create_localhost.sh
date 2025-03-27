#!/bin/bash
# makes and starts a postgres server in the directory /usr/local/var/postgres,
# creates a database called wimbledon on it and runs schema.py to
# define the schema on that database.
POSTGRES_DIR="/usr/local/var/postgres"

if [[ ! -d "${POSTGRES_DIR}" ]]; then
    mkdir -p "${POSTGRES_DIR}"
fi

initdb -D "${POSTGRES_DIR}"

pg_ctl -D "${POSTGRES_DIR}" -l logfile start

createdb wimbledon

if [ -z "$1" ]; then
    # No argument supplied, create a new database
    SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    python "${SCRIPT_DIR}/schema.py"
else
    # Argument supplied, restore the database from the file
    psql wimbledon < $1
fi
