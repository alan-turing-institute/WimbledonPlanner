#!/bin/bash
pg_isready -q -h localhost
online=$?

if [[ ${online} -ne 0 ]]; then
    echo "attempting to start server"
    pg_ctl start -D /usr/local/var/postgres -l logfile
fi

pg_isready -q -h localhost
online=$?

if [[ ${online} -ne 0 ]]; then
    echo "attempting to create server"
    sh create_localhost.sh
fi

pg_isready -q -h localhost
online=$?

if [[ ${online} -ne 0 ]]; then
    echo "failed"
else
    echo "server online"
fi

exit ${online}