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

all: $(FORECAST_CSV) $(HARVEST_CSV) data/figs/.timestamp

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

# generate the plots
data/figs/.timestamp : $(FORECAST_CSV) $(HARVEST_CSV)
	source $(VENV_ACTIVATE) && cd vis && python vis_to_file.py && touch ../data/figs/.timestamp

.PHONY: all
.INTERMEDIATE: forecast_csv harvest_csv
