"""Run this script from the command line whilst in the vis directory to save forecast/harvest visualisations.
Usage:
Save forecast summary plots:
python save.py forecast

Save forecast vs. harvest comparisons:
python save.py harvest

Save individual forecast project/person visualisations:
python save.py forecast individual

Save everything:
python save.py forecast harvest all
"""


# fix matplotlib issue caused by venv with some backends
import matplotlib

try:
    matplotlib.use("TkAgg")
except:
    print("TkAgg backend not present.")
import matplotlib.pyplot as plt

import time
import os.path
import sys
import string
import subprocesse
from datetime import datetime

import pandas as pd

from wimbledon.vis import Visualise


FIG_DIR = "../data/figs"
PROJECTS_DIR = FIG_DIR + "/projects"
PEOPLE_DIR = FIG_DIR + "/people"
HARVEST_DIR = FIG_DIR + "/harvest"


def check_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def save_fig(fig, save_dir, save_name):
    check_dir(save_dir)
    fig.savefig(save_dir + "/" + save_name + ".pdf", bbox_inches="tight")
    plt.close(fig)


def save_sheet(sheet, save_dir, save_name):
    check_dir(save_dir)
    with open(save_dir + "/" + save_name + ".html", "w") as f:
        f.write(sheet)


def init_vis(with_tracked_time=True, update_db=False):
    print("Initialising visualisation object... ", end="", flush=True)
    start = time.time()

    vis = Visualise(with_tracked_time=with_tracked_time, update_db=update_db)

    print("{:.1f}s".format(time.time() - start))
    return vis


def forecast_summary(vis, display="screen"):
    print("Saving Forecast summary plots... ", end="", flush=True)
    start = time.time()

    # sheets
    sheet = vis.whiteboard("person", display=display)
    save_sheet(sheet, PEOPLE_DIR, "people")

    sheet = vis.whiteboard("project", display=display)
    save_sheet(sheet, PROJECTS_DIR, "projects")

    # project summary plots
    fig = vis.heatmap_allocations("PROJECT_REQUIREMENTS", "institute")
    save_fig(fig, PROJECTS_DIR, "Project_Requirements")

    fig = vis.heatmap_allocations("PROJECT_ALLOCATED", "institute")
    save_fig(fig, PROJECTS_DIR, "Project_Allocated")

    fig = vis.heatmap_allocations("PROJECT_RESREQ", "institute")
    save_fig(fig, PROJECTS_DIR, "Project_ResReq")

    # people summary plots
    fig = vis.heatmap_allocations("ALL_PEOPLE", "institute")
    save_fig(fig, PEOPLE_DIR, "People_All_Allocations")

    # capacity plot
    fig = vis.plot_capacity_check()
    save_fig(fig, FIG_DIR, "Capacity_Check")

    print("{:.1f}s".format(time.time() - start))


def whiteboard():
    print("Saving Whiteboard visualisations...", end="", flush=True)
    start = time.time()

    # make poster pdf sheets
    sheet = vis.whiteboard("person", display="print")
    save_sheet(sheet, PEOPLE_DIR, "people")

    sheet = vis.whiteboard("project", display="print")
    save_sheet(sheet, PROJECTS_DIR, "projects")

    try:
        subprocess.call(["sh", "whiteboard_to_pdf.sh"])
    except:
        print("PDF conversion failed.")

    # make screen optimised sheets
    sheet = vis.whiteboard("person", display="screen")
    save_sheet(sheet, PEOPLE_DIR, "people")

    sheet = vis.whiteboard("project", display="screen")
    save_sheet(sheet, PROJECTS_DIR, "projects")

    print("{:.1f}s".format(time.time() - start))


def harvest_vs_forecast(vis):
    # forecast vs. harvest comparisons
    print("Saving Harvest vs. Forecast comparisons... ", end="", flush=True)
    start = time.time()

    for project_id in vis.fc.projects.index:
        name = vis.fc.get_project_name(project_id)

        # strip punctuation (apparently quickest way: https://stackoverflow.com/a/266162)
        name = name.translate(str.maketrans("", "", string.punctuation))

        save_name = name.replace(" ", "_") + "_" + str(project_id)

        try:
            plot = vis.plot_forecast_harvest(
                project_id,
                start_date=datetime.now() - pd.Timedelta("365 days"),
                end_date=datetime.now(),
            )

            save_fig(plot, HARVEST_DIR, save_name)

        except ValueError:
            pass
        except TypeError:
            pass

    print("{:.1f}s".format(time.time() - start))


def forecast_individual(vis):
    print("Saving Forecast individual plots... ", end="", flush=True)
    start = time.time()

    # plots for individual people
    for person_id in vis.fc.people.index:
        name = vis.fc.get_person_name(person_id)
        save_name = name.replace(" ", "_") + "_" + str(person_id)

        plot = vis.plot_allocations(person_id, "person")
        if plot is not None:
            save_fig(plot, PEOPLE_DIR + "/individual", save_name + "_plot")

        heatmap = vis.heatmap_allocations(person_id, "person")
        if heatmap is not None:
            save_fig(heatmap, PEOPLE_DIR + "/individual", save_name + "_heatmap")

    # plots for individual projects
    for project_id in vis.fc.projects.index:
        name = vis.fc.get_project_name(project_id)

        # strip punctuation (apparently quickest way: https://stackoverflow.com/a/266162)
        name = name.translate(str.maketrans("", "", string.punctuation))

        save_name = name.replace(" ", "_") + "_" + str(project_id)

        plot = vis.plot_allocations(project_id, "project")
        if plot is not None:
            save_fig(plot, PROJECTS_DIR + "/individual", save_name + "_plot")

        heatmap = vis.heatmap_allocations(project_id, "project")
        if heatmap is not None:
            save_fig(heatmap, PROJECTS_DIR + "/individual", save_name + "_heatmap")

    print("{:.1f}s".format(time.time() - start))


if __name__ == "__main__":
    args = sys.argv[1:]

    if "harvest" in args:
        with_tracked_time = True
    else:
        with_tracked_time = False

    if "update" in args:
        update_db = True
    else:
        update_db = False

    vis = init_vis(with_tracked_time=with_tracked_time, update_db=update_db)

    if "forecast" in args and "individual" in args:
        forecast_individual(vis)

    elif "forecast" in args and "all" in args:
        forecast_summary(vis)
        forecast_individual(vis)

    elif "forecast" in args:
        forecast_summary(vis)

    elif "whiteboard" in args:
        whiteboard()

    if "harvest" in args:
        harvest_vs_forecast(vis)
