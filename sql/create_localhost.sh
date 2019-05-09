#!/bin/bash
# makes and starts a postgres server in the directory ../data/sql

if [[ ! -d "../data/sql" ]]; then
    mkdir "../data/sql"
fi

initdb -D ../data/sql

sh start_localhost.sh