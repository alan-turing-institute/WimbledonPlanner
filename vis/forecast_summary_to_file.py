import time
start = time. time()

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

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def save_fig(fig, save_dir, save_name, dpi=300):
    check_dir(save_dir)
    fig.savefig(save_dir+'/'+save_name+'.pdf', bbox_inches='tight')
    plt.close(fig)


def save_sheet(sheet, save_dir, save_name):
    check_dir(save_dir)
    with open(save_dir + '/' + save_name + '.html', 'w') as f:
        f.write(sheet.render())


FIG_DIR = '../data/figs'
PROJECTS_DIR = FIG_DIR + '/projects'
PEOPLE_DIR = FIG_DIR + '/people'

print('='*50)
print('Initialising visualisation object')
vis = Visualise(init_harvest=False)

# sheets
print('='*50)
print('Sheets')

sheet = vis.styled_sheet('person')
save_sheet(sheet, PEOPLE_DIR, 'people')

sheet = vis.styled_sheet('project')
save_sheet(sheet, PROJECTS_DIR, 'projects')

# project summary plots
print('='*50)
print('Project summary')

fig = vis.heatmap_allocations('PROJECT_REQUIREMENTS', 'institute')
save_fig(fig, PROJECTS_DIR, 'Project_All_Requirements')

fig = vis.heatmap_allocations('PROJECT_TOTALS', 'institute')
save_fig(fig, PROJECTS_DIR, 'Project_All_Totals')

fig = vis.heatmap_allocations('PROJECT_NETALLOC', 'institute')
save_fig(fig, PROJECTS_DIR, 'Project_All_Netalloc')

# people summary plots
print('='*50)
print('People summary')

fig = vis.heatmap_allocations('ALL_PEOPLE', 'institute')
save_fig(fig, PEOPLE_DIR, 'People_All_Allocations')

# capacity plot
print('='*50)
print('Capacity')

fig = vis.plot_capacity_check()
save_fig(fig, FIG_DIR, 'Capacity_Check')

print('='*50)
print('DONE! ({:.1f}s)'.format(time.time()-start))
