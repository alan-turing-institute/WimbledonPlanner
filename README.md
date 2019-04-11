# Project Wimbledon

Project Wimbledon is an attempt to fix and possibly automate the REG group's
planning and billing process.

## Configuration

The file `api/config.py` must be created, containing the API tokens/authorisation info for Harvest and Forecast. It should contain two dictionaries as follows:

```python
forecast = {'account_id': '974183',
            'auth_token': '<YOUR_FORECAST_TOKEN>'}


harvest = {"account_id": "968445",
           "access_token": "<YOUR_HARVEST_TOKEN>",
           "email": "<YOUR_EMAIL>"}
```

To get the tokens: 
1) Go to https://id.getharvest.com/developers and login (ask Oliver about making an account if you don't have one).
2) Click "Create New Personal Access Token"
3) Give the token some imaginative name.
4) Under "Choose Account" select "Forecast - The Alan Turing Institute"
5) Copy the token into config.py
5) Repeat steps 2 to 5, this time selecting "Harvest - The Alan Turing Institute" under "Choose Account".

## Usage

To create a python venv with requirements installed, download the latest Forecast and Harvest data, and save many Forecast/Harvest visualisations to file, run:
```bash
> make
```

Running `make` subsequent times will not trigger anything to be updated. To force everything to update run:
```bash
> make clean
> make
```

Alternatively, to update the Forecast data only, and save summary Forecast figures only (including the whiteboard-style visualisations), run:
```bash
> make forecast 
```
The above is much quicker than `make` (few seconds rather than few minutes), and `make forecast` always triggers the data and figures to be updated (i.e. the initial `make clean` step is not required on subsequent runs.)



## Interactive Notebooks

The Jupyter notebooks `vis/visualise_forecast.ipynb` and `vis/visualise_harvest.ipynb` load (but don't update) the Harvest/Forecast data and displays the visualisations, including some interactive widgets to customise/display plots for individual projects, individual people etc.
