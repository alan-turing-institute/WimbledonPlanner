import time
import os.path
import sys

import pandas as pd

from wimbledon.vis.Visualise import Visualise

FIG_DIR = '../data/figs'
PROJECTS_DIR = FIG_DIR + '/projects'
PEOPLE_DIR = FIG_DIR + '/people'


def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def save_sheet(sheet, save_dir, save_name):
    check_dir(save_dir)
    with open(save_dir + '/' + save_name + '.html', 'w') as f:
        f.write(sheet)


def whiteboard(vis, display='screen'):
    print('Creating Whiteboard visualisations... ', end='', flush=True)
    start = time.time()

    # make whiteboard html
    sheet = vis.whiteboard('person', display=display)
    save_sheet(sheet, PEOPLE_DIR, 'people')

    sheet = vis.whiteboard('project', display=display)
    save_sheet(sheet, PROJECTS_DIR, 'projects')

    print('{:.1f}s'.format(time.time() - start))


if __name__ == '__main__':
    print('Initialising visualisation object... ', end='', flush=True)
    init = time.time()

    if len(sys.argv) > 1:
        start_date = pd.to_datetime(sys.argv[1])
    else:
        start_date = pd.datetime.now() - pd.Timedelta('30 days')

    if len(sys.argv) > 2:
        end_date = pd.to_datetime(sys.argv[2])
    else:
        end_date = start_date + pd.Timedelta('395 days')

    if len(sys.argv) > 3:
        display = sys.argv[3]
    else:
        display = 'screen'

    vis = Visualise(init_forecast=True, init_harvest=False,
                    start_date=start_date, end_date=end_date)

    print('{:.1f}s'.format(time.time() - init))

    whiteboard(vis, display)


