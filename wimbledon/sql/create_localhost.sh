#!/bin/bash
# makes and starts a postgres server in the directory /usr/local/var/postgres,
# creates a database called wimbledon on it, runs schema.py to
# define the schema on that database and update_db.py to upload data to it.

if [[ ! -d "/usr/local/var/postgres" ]]; then
    mkdir "/usr/local/var/postgres"
fi

initdb -D /usr/local/var/postgres

bash start_localhost.sh

createdb wimbledon

python schema.py

python update_db.py