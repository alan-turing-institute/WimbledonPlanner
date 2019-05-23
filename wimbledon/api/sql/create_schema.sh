#!/bin/bash
# creates tables for forecast and harvest data models on the database defined by host, port, username and dbname
# or pass -c localhost or -c azure to use pre-set configs

host="localhost"
port=""
username=""
dbname="wimbledon"

while [[ "$1" != "" ]]; do
    case $1 in
        -c | --config )         shift
                                if [[ "$1" = "localhost" ]]; then
                                    host="localhost"
                                    port=""
                                    username=""
                                    dbname="wimbledon"
                                elif [[ "$1" = "azure" ]]; then
                                    host="wimbledon-planner.postgres.database.azure.com"
                                    port="5432"
                                    username="jack@wimbledon-planner"
                                    dbname="wimbledon"
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
        * )                     exit 1
    esac
    shift
done

if [[ "$1" = "localhost" ]]; then
    sh start_localhost.sh
fi

createdb --host=${host} --port=${port} --username=${username} ${dbname}

psql --host=${host} --port=${port} --username=${username} --dbname=${dbname} -f schema.sql
