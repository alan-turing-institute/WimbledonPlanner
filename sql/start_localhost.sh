#!/bin/bash
pg_isready -q -h localhost
online=$?

if [[ ${online} -ne 0 ]]; then
    echo "starting server"
    pg_ctl start -l ../data/sql/logfile -D ../data/sql
fi

pg_isready -q -h localhost
online=$?

if [[ ${online} -ne 0 ]]; then
    echo "FAILED"
else
    echo "server online"
fi

exit ${online}