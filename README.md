# Project Wimbledon

Project Wimbledon is an attempt to fix and possibly automate the REG group's
planning and billing process.

Recent versions of the "whiteboard" visualisation can be found on SharePoint here:

* [Projects sheet](https://thealanturininstitute.sharepoint.com/:u:/s/ResearchEngineering/EawBPLOCSQVHvmQNwuz5Nd8Bv8leoZ5TjFXRE_TUtwvo7A?e=gUr6GO)

* [People sheet](https://thealanturininstitute.sharepoint.com/:u:/s/ResearchEngineering/EfI1jsHdKkNLsUoMa6lOc2gBgyPOtKigueTbnYXwHtFxnQ?e=VQkdTV)

## Requirements

Python package dependencies are listed in requirements.txt and are automatically installed to the python virtual environment
created when running make (see below).

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

The file `api/secrets.py` must be created, containing the API tokens/authorisation info for Harvest and Forecast.
This file should contain two dictionaries as follows:

```python
harvest_api_credentials = {
    "harvest_account_id": "<HARVEST_ACCOUNT_ID>",
    "forecast_account_id": "<FORECAST_ACCOUNT_ID>",
    "access_token": "<ACCESS_TOKEN>"
}
```

To get the tokens:
1) Go to https://id.getharvest.com/developers and login (ask Oliver about making an account if you don't have one).
2) Click "Create New Personal Access Token"
3) Name the token after the machine you are creating the `secrets.py` file on.
4) To get the Harvest account key, ensure that you have selected "Harvest - The Alan Turing Institute" under "Choose Account"
5) To get the Forecast account key, ensure that you have selected "Forecast - The Alan Turing Institute" under "Choose Account"

This file **must not be checked into version control** and is listed in the repository's `.gitignore` file to ensure it is not.
If you rename this file, make sure to update it's entry in the `.gitignore` file.

## Quickstart

Browse to the `WimbledonPlanner` directory then double click on `run_whiteboard.command` to create the whiteboard visualisations from the latest Forecast data.
The visualisastions are saved in `data/figs/projects` and `data/figs/people`.

## Usage with make

To create a python venv with requirements installed, download the latest Forecast and Harvest data, and save many Forecast/Harvest visualisations to file, run:
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

The above `make forecast` and `make whiteboard` are much quicker than `make` (few seconds rather than few minutes), and always trigger the data to be updated (i.e. the initial `make clean` step is not required on subsequent runs.)

## Usage with Python

Rather than using make you can also run the python scripts individually yourself.

**To update the data:**

*Forecast (saved to `data/forecast`):*
```bash
> cd api/
> python update.py forecast
```

*Harvest (saved to `data/harvest`):*
```bash
> cd api/
> python update.py harvest
```

*Forecast and Harvest:*
```bash
> cd api/
> python update.py forecast harvest
```

**To create the visualisations (saved to `data/figs`):**

*Whiteboard visualisations (as PDF and HTML):*
```bash
> cd vis
> python save.py whiteboard
```

*Forecast summary plots:*
```bash
> cd vis
> python save.py forecast
```

*All forecast plots:*
```bash
> cd vis
> python save.py forecast all
```

*Harvest vs. Forecast comparisons:*
```bash
> cd vis
> python save.py harvest
```

*Everything:*
```bash
> cd vis
> python save.py forecast harvest all
```

## Interactive Notebooks

The Jupyter notebooks `vis/visualise_forecast.ipynb` and `vis/visualise_harvest.ipynb` load (but don't update) the Harvest/Forecast data and displays the visualisations, including some interactive widgets to customise/display plots for individual projects, individual people etc.
