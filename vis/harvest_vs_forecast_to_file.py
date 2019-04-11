# fix matplotlib issue caused by venv with some backends
import matplotlib
default_backend = matplotlib.get_backend()
try:
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
except:
    print('TkAgg backend not present.')
    matplotlib.use(default_backend)
    import matplotlib.pyplot as plt

from Visualise import Visualise
import os.path
import string
import pandas as pd

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def save_fig(fig, save_dir, save_name):
    check_dir(save_dir)
    fig.savefig(save_dir+'/'+save_name+'.pdf', bbox_inches='tight')
    plt.close(fig)


FIG_DIR = '../data/figs'
PROJECTS_DIR = FIG_DIR + '/projects'
PEOPLE_DIR = FIG_DIR + '/people'
HARVEST_DIR = FIG_DIR + '/harvest'

print('='*50)
print('Initialising visualisation object')
vis = Visualise()

# forecast vs. harvest comparisons
print('='*50)
print('Harvest vs. forecast comparisons')

for project_id in vis.fc.projects.index:
    name = vis.fc.get_project_name(project_id)

    # strip punctuation (apparently quickest way: https://stackoverflow.com/a/266162)
    name = name.translate(str.maketrans('', '', string.punctuation))

    save_name = name.replace(' ', '_') + '_' + str(project_id)

    try:
        plot = vis.plot_forecast_harvest(project_id,
                                         start_date=pd.datetime.now() - pd.Timedelta('365 days'),
                                         end_date=pd.datetime.now())

        save_fig(plot, HARVEST_DIR, save_name)

    except ValueError as e:
        print(e)
    except TypeError as e:
        print(e)

print('='*50)
print('DONE!')
