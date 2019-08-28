#!/bin/bash
# makes and starts a postgres server in the directory /usr/local/var/postgres,
# creates a database called wimbledon on it and runs schema.py to
# define the schema on that database.

if [[ ! -d "/usr/local/var/postgres" ]]; then
    mkdir "/usr/local/var/postgres"
fi

pg_ctl -D /usr/local/var/postgres -l logfile start

initdb -D /usr/local/var/postgres

createdb wimbledon

python schema.py
