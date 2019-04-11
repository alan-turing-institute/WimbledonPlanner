# Makefile for WimbledonPlanner (Turing REG team planning process).
# Use to produce:
#  - the raw data from the harvest/forecast api in csv format
#  - (TODO) a database containing this data
#  - various figures (including the whiteboard visualization)

SHELL := /bin/bash

# python activate virtual env
VENV_ACTIVATE = venv/bin/activate

FORECAST_CSV_BASE = assignments.csv connections.csv people.csv projects.csv \
clients.csv milestones.csv placeholders.csv roles.csv 

HARVEST_CSV_BASE = clients.csv roles.csv tasks.csv user_assignments.csv \
projects.csv task_assignments.csv time_entries.csv users.csv

FORECAST_CSV = $(addprefix data/forecast/,$(FORECAST_CSV_BASE))
HARVEST_CSV = $(addprefix data/harvest/,$(HARVEST_CSV_BASE))

## default: make all plots, but don't clean
all: forecast_plots combined_plots 

## build the summary plots with fresh data
refresh_forecast: clean_csv forecast_summary

# set up the python virtual environment
$(VENV_ACTIVATE): requirements.txt
	python -m venv ./venv && source $@ && pip install -Ur requirements.txt

$(FORECAST_CSV) : forecast_csv ;
$(HARVEST_CSV) : harvest_csv ;

# generate the csv data
forecast_csv : $(VENV_ACTIVATE)
	mkdir -p data/forecast && source $(VENV_ACTIVATE) && cd api && python forecast_api.py

harvest_csv : $(VENV_ACTIVATE)
	mkdir -p data/harvest && source $(VENV_ACTIVATE) && cd api && python harvest_api.py

data/figs/.forecast_summary_timestamp : $(FORECAST_CSV)
	source $(VENV_ACTIVATE) && cd vis && python forecast_summary_to_file.py && \
	touch ../data/figs/.forecast_summary_timestamp

data/figs/.forecast_individual_timestamp : $(FORECAST_CSV)
	source $(VENV_ACTIVATE) && cd vis && python forecast_individual_to_file.py && \
	touch ../data/figs/.forecast_individual_timestamp

data/figs/.harvest_vs_forecast_timestamp : $(HARVEST_CSV) $(FORECAST_CSV)
	source $(VENV_ACTIVATE) && cd vis && python harvest_vs_forecast_to_file.py && \
	touch ../data/figs/.harvest_vs_forecast_timestamp


forecast_summary: data/figs/.forecast_summary_timestamp

forecast_plots: data/figs/.forecast_summary_timestamp data/figs/.forecast_individual_timestamp

combined_plots: data/figs/.harvest_vs_forecast_timestamp

clean_csv:
	rm -rf $(FORECAST_CSV) $(HARVEST_CSV)

.PHONY: all combined_plots forecast_plots forecast_summary
.INTERMEDIATE: forecast_csv harvest_csv 
