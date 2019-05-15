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
    print('Saving Whiteboard visualisations...', end='', flush=True)
    start=time.time()

    # make poster pdf sheets
    sheet = vis.styled_sheet('person', display='print')
    save_sheet(sheet, PEOPLE_DIR, 'people')

    sheet = vis.styled_sheet('project', display='print')
    save_sheet(sheet, PROJECTS_DIR, 'projects')

    print('{:.1f}s'.format(time.time() - start))


if __name__ == '__main__':
    args = sys.argv[1:]

    start_date = pd.to_datetime(sys.argv[1])
    end_date = pd.to_datetime(sys.argv[2])
    print(start_date)
    print(end_date)

    vis = Visualise(init_forecast=True, init_harvest=False,
                    start_date=start_date, end_date=end_date)

    whiteboard(vis)


