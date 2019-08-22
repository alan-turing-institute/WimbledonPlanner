"""Run this script to update database from the harvest and forecast apis.
Usage:

Without updating time tracking:
python update.py

Including time tracking update:
python update.py harvest
"""

import sys
from wimbledon.harvest.db_interface import update_db
import time

start = time.time()

if 'harvest' in sys.argv:
    with_tracked_time = True
else:
    with_tracked_time = False

update_db(with_tracked_time=with_tracked_time)

print('='*50)
print('TOTAL UPDATE TIME: {:.1f}s'.format(time.time() - start))
