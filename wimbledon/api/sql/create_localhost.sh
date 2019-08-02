#!/bin/bash
# makes and starts a postgres server in the directory ../data/sql

if [[ ! -d "/usr/local/var/postgres" ]]; then
    mkdir "/usr/local/var/postgres"
fi

initdb -D /usr/local/var/postgres

bash start_localhost.sh