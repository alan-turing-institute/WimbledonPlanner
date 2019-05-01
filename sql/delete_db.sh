#!/bin/bash
psql --host=wimbledon-planner.postgres.database.azure.com --port=5432 --username=jack@wimbledon-planner --dbname=postgres -f delete_db.sql
