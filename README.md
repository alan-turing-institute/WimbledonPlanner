# Project Wimbledon

Project Wimbledon is an attempt to fix and possibly automate the REG group's
planning and billing process.

## Usage

To create a python venv with requirements installed, download the latest Forecast and Harvest data, and save many Forecast/Harvest visualisations to file, run:
```bash
> make
```

To update the Forecast data only, and save summary Forecast figures only (including the whiteboard-style visualisations), run:
```bash
> make -f make_forecast 
```

Subsequent runs of `make -f make-forecast` will update the Forecast data and figures. Subsequent runs of `make` will not trigger data/figure updates.

## Interactive Notebooks

The Jupyter notebooks `vis/visualise_forecast.ipynb` and `vis/visualise_harvest.ipynb` load (but don't update) the Harvest/Forecast and displays the visualisations, including some interactive widgets to customise/display plots for individual projects, individual people etc.
