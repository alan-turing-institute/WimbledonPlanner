# Project Wimbledon

Project Wimbledon is an attempt to fix and possibly automate the REG group's
planning and billing process.

Recent versions of the "whiteboard" visualisation can be found here:

* [Projects sheet](https://wimbledon-planner.azurewebsites.net/projects)

* [People sheet](https://wimbledon-planner.azurewebsites.net/people)

To update the versions hosted here go to https://wimbledon-planner.azurewebsites.net/update. This will take a couple of minutes after which you should get the message "DATA UPDATED!".

## Requirements

Python package dependencies are listed in requirements.txt and can be installed to a python virtual environment automatically using the make file (see below), or by running this from the wimbledon directory:
```bash
> pip install -r requirements.txt
```

For converting the HTML whiteboard visualisations to PDFs the command line tool `wkhtmltopdf` is required.
To install it on Mac OS (assuming `brew` is installed) run:
```bash
> brew cask install wkhtmltopdf
```

You may also need to install ghostscript with:
```bash
> brew install ghostscript
```

`brew` can be installed from the Turing self service app, or from here: https://brew.sh/

## Configuration

Wimbledon requires a Harvest account ID and token as part of its configuration. This is stored in the file 
`~/.wimbledon/.harvest_credentials`, which is a json file with the following structure:
```json
{"harvest_account_id":  "<HARVEST_ACCOUNT_ID",
 "forecast_account_id":  "<FORECAST_ACCOUNT_ID",
 "access_token": "<ACCESS_TOKEN>"}
```

You can either create this file yourself or use the `set_harvest_credentials` function in `wimbledon/config.py`.
Alternatively (e.g. for the Azure app) they can be stored in the environment variables `HARVEST_ACCOUNT_ID`, `FORECAST_ACCOUNT_ID` and `HARVEST_ACCESS_TOKEN`.

To get the tokens:
1) Go to https://id.getharvest.com/developers and login (ask Oliver about making an account if you don't have one).
2) Click "Create New Personal Access Token"
3) Name the token after the machine you are creating the `secrets.py` file on.
4) To get the Harvest account key, ensure that you have selected "Harvest - The Alan Turing Institute" under "Choose Account"
5) To get the Forecast account key, ensure that you have selected "Forecast - The Alan Turing Institute" under "Choose Account"

This file **must not be checked into version control** and is stored in a separate directory and listed in the
 repository's `.gitignore` file to ensure it is not.

## Quickstart

Browse to the `WimbledonPlanner/scripts` directory then double click on `run_whiteboard.command` to create the
 whiteboard visualisations from the latest Forecast data. The visualisastions are saved in `data/figs/projects` 
 and `data/figs/people`.

## Interactive Notebooks

The Jupyter notebooks `visualise_forecast.ipynb` and `visualise_harvest.ipynb` in the `notebooks` directory get the
 latest Harvest/Forecast data and display the visualisations, including some interactive widgets
  to customise/display plots for individual projects, individual people etc. 
  
 The `reg_capacity_vs_demand.ipynb` notebook creates the capacity vs. demand history plot originally used for the
  Trustee board report.

## Usage with make

To create a python venv with requirements installed, download the latest Forecast and Harvest data, and save
 many Forecast/Harvest visualisations to file, run (from the `WimbledonPlanner` directory):
```bash
> make
```

Running `make` subsequent times will not trigger anything to be updated. To force everything to update run:
```bash
> make clean
> make
```

Alternatively, to update the Forecast data only, and save summary Forecast figures only, run:
```bash
> make forecast
```

Or to update the Forecast data and save the whiteboard visualisations only:
```bash
> make whiteboard
```

The above `make forecast` and `make whiteboard` are much quicker than `make` (few seconds rather than few minutes), 
and always trigger the data to be updated (i.e. the initial `make clean` step is not required on subsequent runs.)

## Usage with Python

Rather than using make you can also run the python scripts individually yourself.

**To update the data:**

*Forecast (saved to `data/forecast`):*
```bash
> cd scripts/
> python update.py forecast
```

*Harvest (saved to `data/harvest`):*
```bash
> cd scripts/
> python update.py harvest
```

*Forecast and Harvest:*
```bash
> cd scripts/
> python update.py forecast harvest
```

**To create the visualisations (saved to `data/figs`):**

*Whiteboard visualisations (as PDF and HTML):*
```bash
> cd scripts/
> python save.py whiteboard
```

*Forecast summary plots:*
```bash
> cd scripts/
> python save.py forecast
```

*All forecast plots:*
```bash
> cd scripts/
> python save.py forecast all
```

*Harvest vs. Forecast comparisons:*
```bash
> cd scripts/
> python save.py harvest
```

*Everything:*
```bash
> cd scripts/
> python save.py forecast harvest all
```
