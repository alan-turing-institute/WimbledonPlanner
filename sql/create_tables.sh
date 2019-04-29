#!/usr/bin/env bash
export PGPASSWORD=Wf80GBRsZv9HjndH5yYdXox3vmIfkcWa

createdb --host=wimbledon-planner.postgres.database.azure.com --port=5432 --username=jack@wimbledon-planner wimbledon

psql --host=wimbledon-planner.postgres.database.azure.com --port=5432 --username=jack@wimbledon-planner --dbname=wimbledon -f harvest.sql

psql --host=wimbledon-planner.postgres.database.azure.com --port=5432 --username=jack@wimbledon-planner --dbname=wimbledon -f forecast.sql