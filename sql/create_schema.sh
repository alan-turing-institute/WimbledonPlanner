#!/bin/bash
createdb --host=wimbledon-planner.postgres.database.azure.com --port=5432 --username=jack@wimbledon-planner wimbledon

psql --host=wimbledon-planner.postgres.database.azure.com --port=5432 --username=jack@wimbledon-planner --dbname=wimbledon -f schema.sql
