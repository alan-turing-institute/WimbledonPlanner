#!/bin/bash

config="localhost"

while [[ "$1" != "" ]]; do
    case $1 in
        -c | --config )         shift
                                if [[ "$1" = "localhost" ]]; then
                                    config="localhost"
                                elif [[ "$1" = "azure" ]]; then
                                    config="azure"
                                fi
                                break
                                ;;
        * )                     exit 1
    esac
    shift
done

echo ${config}

if [[ "$1" = "localhost" ]]; then
    sh start_localhost.sh
fi

echo "Deleting original database"
bash delete_db.sh --config ${config}

echo "Recreating database schema"
bash create_schema.sh --config ${config}