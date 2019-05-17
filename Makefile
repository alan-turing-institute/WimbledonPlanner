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

help:
	@echo 'targets:'
	@echo 'all (default)    - Generate all plots (slow)'
	@echo 'forecast         - Fetch latest Forecast csv data and generate Forecast summary plots'
	@echo 'clean            - Remove csv data'
	@echo 'whiteboard       - Make the wallchart/whiteboard plots'
	@echo 'forecast_summary - Generate Forecast summary plots using present csv data (quick)'
	@echo 'forecast_plots   - Generate full set of Forecast plots'
	@echo 'combined_plots   - Generate Harvest/Forecast comparison plots (slow)'
	@echo 'forecast_csv and - Fetch csv data only. Might need to "make clean" for this to take effect.'
	@echo 'harvest_csv        Fetching the Harvest data can take some time'

## build the summary plots with fresh data
forecast: clean forecast_summary

## build the whiteboard visualisations with fresh data
whiteboard: clean whiteboard_plots

# set up the python virtual environment
$(VENV_ACTIVATE): requirements.txt
	python3 -m venv ./venv && source $@ && pip3 install -Ur requirements.txt

$(FORECAST_CSV) : forecast_csv ;
$(HARVEST_CSV) : harvest_csv ;

# generate the csv data
forecast_csv : $(VENV_ACTIVATE)
	mkdir -p data/forecast && source $(VENV_ACTIVATE) && cd api && python update.py forecast

harvest_csv : $(VENV_ACTIVATE)
	mkdir -p data/harvest && source $(VENV_ACTIVATE) && cd api && python update.py harvest


data/figs/.forecast_summary_timestamp : $(FORECAST_CSV)
	source $(VENV_ACTIVATE) && cd vis && python save.py forecast && \
	touch ../data/figs/.forecast_summary_timestamp

data/figs/.forecast_individual_timestamp : $(FORECAST_CSV)
	source $(VENV_ACTIVATE) && cd vis && python save.py forecast individual && \
	touch ../data/figs/.forecast_individual_timestamp

data/figs/.harvest_vs_forecast_timestamp : $(HARVEST_CSV) $(FORECAST_CSV)
	source $(VENV_ACTIVATE) && cd vis && python save.py harvest && \
	touch ../data/figs/.harvest_vs_forecast_timestamp

data/figs/projects/projects.pdf : $(FORECAST_CSV)
	source $(VENV_ACTIVATE) && \
	cd vis/ && \
	python save.py whiteboard

forecast_summary: data/figs/.forecast_summary_timestamp

forecast_plots: data/figs/.forecast_summary_timestamp data/figs/.forecast_individual_timestamp

combined_plots: data/figs/.harvest_vs_forecast_timestamp

whiteboard_plots: data/figs/projects/projects.pdf

clean:
	rm -rf $(FORECAST_CSV) $(HARVEST_CSV)

.PHONY: all whiteboard whiteboard_plots combined_plots forecast_plots forecast_summary forecast clean
.INTERMEDIATE: forecast_csv harvest_csv 
