"""Run this script from the command line whilst in the api directory to update harvest and forecast data.
Usage:
Update forecast data:
python update.py forecast

Update harvest data:
python update.py harvest

Update forecast and harvest data:
python update.py forecast harvest
or
python update.py harvest forecast
"""

import sys
import wimbledon.api.DataUpdater
import time

start = time.time()

for arg in sys.argv[1:]:
    if arg == 'harvest':
        print('='*50)
        print('UPDATING HARVEST')
        print('='*50)
        wimbledon.api.DataUpdater.update_to_csv('../data', run_forecast=False, run_harvest=True)

    elif arg == 'forecast':
        print('='*50)
        print('UPDATING FORECAST')
        print('='*50)
        wimbledon.api.DataUpdater.update_to_csv('../data', run_forecast=True, run_harvest=False)

    else:
        raise ValueError('Invalid argument. Valid options are harvest and forecast.')

print('='*50)
print('TOTAL UPDATE TIME: {:.1f}s'.format(time.time() - start))
