import time
import os.path
import sys

import pandas as pd

from Visualise import Visualise

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


def whiteboard(vis):
    print('Creating Whiteboard visualisations... ', end='', flush=True)
    start = time.time()

    # make poster pdf sheets
    sheet = vis.styled_sheet('person', display='print')
    save_sheet(sheet, PEOPLE_DIR, 'people')

    sheet = vis.styled_sheet('project', display='print')
    save_sheet(sheet, PROJECTS_DIR, 'projects')

    print('{:.1f}s'.format(time.time() - start))


if __name__ == '__main__':
    print('Initialising visualisation object... ', end='', flush=True)
    init = time.time()

    if len(sys.argv)>1:
        start_date = pd.to_datetime(sys.argv[1])
    else:
        start_date = pd.datetime.now() - pd.Timedelta('30 days')

    if len(sys.argv)>2:
        end_date = pd.to_datetime(sys.argv[2])
    else:
        end_date = start_date + pd.Timedelta('395 days')

    vis = Visualise(init_forecast=True, init_harvest=False,
                    start_date=start_date, end_date=end_date)

    print('{:.1f}s'.format(time.time() - init))

    whiteboard(vis)


