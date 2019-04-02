from Visualise import Visualise
import string
import matplotlib.pyplot as plt

def save_fig(fig, save_dir, save_name, dpi=300):
    fig.savefig(save_dir+'/'+save_name+'.png', dpi=dpi, bbox_inches='tight')
    plt.close(fig)

def save_sheet(sheet, save_dir, save_name):
    sheet.to_excel(save_dir + '/' + save_name + '.xlsx')
    with open(save_dir + '/' + save_name + '.html', 'w') as f:
        f.write(sheet.render())


FIG_DIR = '../data/figs'
PROJECTS_DIR = FIG_DIR + '/projects'
PEOPLE_DIR = FIG_DIR + '/people'

vis = Visualise()

# sheets
print('Sheets')

sheet = vis.styled_sheet('person')
save_sheet(sheet, PEOPLE_DIR, 'people')

sheet = vis.styled_sheet('project')
save_sheet(sheet, PROJECTS_DIR, 'projects')

# project summary plots
print('Project summary')

fig = vis.heatmap_allocations('ALL_REQUIREMENTS','project')
save_fig(fig, PROJECTS_DIR, 'Project_All_Requirements')

fig = vis.heatmap_allocations('ALL_TOTALS', 'project')
save_fig(fig, PROJECTS_DIR, 'Project_All_Totals')

fig = vis.heatmap_allocations('ALL_NETALLOC', 'project')
save_fig(fig, PROJECTS_DIR, 'Project_All_Netalloc')

# people summary plots
print('People summary')

fig = vis.heatmap_allocations('ALL', 'person')
save_fig(fig, PEOPLE_DIR, 'People_All_Allocations')

# capacity plot
print('Capacity')

fig = vis.plot_capacity_check()
save_fig(fig, FIG_DIR, 'Capacity_Check')

# plots for individual people
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
