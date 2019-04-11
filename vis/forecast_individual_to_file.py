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
vis = Visualise(init_harvest=False)

# plots for individual people
print('='*50)
print('Individual people')

for person_id in vis.fc.people.index:
    name = vis.fc.get_person_name(person_id)
    save_name = name.replace(' ', '_') + '_' + str(person_id)

    plot = vis.plot_allocations(person_id, 'person')
    if plot is not None:
        save_fig(plot, PEOPLE_DIR + '/individual', save_name + '_plot')

    heatmap = vis.heatmap_allocations(person_id, 'person')
    if heatmap is not None:
        save_fig(heatmap, PEOPLE_DIR + '/individual', save_name + '_heatmap')

# plots for individual projects
print('='*50)
print('Individual projects')

for project_id in vis.fc.projects.index:
    name = vis.fc.get_project_name(project_id)

    # strip punctuation (apparently quickest way: https://stackoverflow.com/a/266162)
    name = name.translate(str.maketrans('', '', string.punctuation))

    save_name = name.replace(' ', '_') + '_' + str(project_id)

    plot = vis.plot_allocations(project_id, 'project')
    if plot is not None:
        save_fig(plot, PROJECTS_DIR + '/individual', save_name + '_plot')

    heatmap = vis.heatmap_allocations(project_id, 'project')
    if heatmap is not None:
        save_fig(heatmap, PROJECTS_DIR + '/individual', save_name + '_heatmap')
