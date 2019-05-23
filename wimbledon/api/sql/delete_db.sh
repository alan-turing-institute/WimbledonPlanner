#!/bin/bash
# delete the wimbledon database (and all its tables) from  a server
host="localhost"
port=""
username=""
dbname="postgres"

while [[ "$1" != "" ]]; do
    case $1 in
        -c | --config )         shift
                                if [[ "$1" = "localhost" ]]; then
                                    host="localhost"
                                    port=""
                                    username=""
                                    dbname="postgres"
                                elif [[ "$1" = "azure" ]]; then
                                    host="wimbledon-planner.postgres.database.azure.com"
                                    port="5432"
                                    username="jack@wimbledon-planner"
                                    dbname="postgres"
                                fi
                                break
                                ;;
        -h | --host )           shift
                                host=$1
                                ;;
        -p | --port )           shift
                                port=$1
                                ;;
        -d | --database )       shift
                                dbname=$1
                                ;;
        -u | --username )       shift
                                username=$1
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

if [[ "$1" = "localhost" ]]; then
    sh start_localhost.sh
fi

psql --host=${host} --port=${port} --username=${username} --dbname=${dbname} -f delete_db.sql