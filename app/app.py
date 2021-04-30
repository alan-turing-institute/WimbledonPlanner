import os
import zipfile
import traceback
import subprocess
import sys
from datetime import datetime

from flask import Flask, send_from_directory, send_file, render_template

from wimbledon.vis import Visualise
from wimbledon.github import preferences_availability as pref

# change matplotlib backend to avoid it trying to pop up figure windows
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt


# Initialise Flask App
app = Flask(__name__)


def check_dir(directory):
    """Check whether a directory exists, if not make it.

    Arguments:
        directory {str} -- path to desired directory.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


@app.route("/")
def home():
    if os.path.isfile(app.config.get("DATA_DIR") + "/.last_update"):
        with open(app.config.get("DATA_DIR") + "/.last_update", "r") as f:
            updated_at = f.read()
    else:
        updated_at = "Never"

    return render_template("index.html", updated_at=updated_at)


@app.route("/update")
def update(update_db=True):
    """Query the Forecast API for the latest data and update the whiteboard
    visualisations.

    Raises:
        ValueError: Traceback of what went wrong if something fails during
         update process.

    Returns:
        str -- a data updated message (or error string if failed)
    """
    try:
        # time update was triggered
        # TODO: make this timezone robust (e.g. make it UK time not local
        #  system time?)
        updated_at = datetime.now().strftime("%d %b %Y, %H:%M")

        vis = Visualise(with_tracked_time=False, update_db=update_db)

        # Generate preference table
        print("Generate preference table...")
        preferences_table = pref.get_all_preferences_table(
            wim=vis.wim, first_date=vis.START_DATE, last_date=vis.END_DATE
        )

        # Save preference table to file
        check_dir(app.config.get("DATA_DIR") + "/figs/preferences")

        with open(
            app.config.get("DATA_DIR") + "/figs/preferences/preferences.html", "w"
        ) as f:
            f.write(preferences_table)

        # Generate whiteboards
        print("Generate whiteboards...")
        whiteboards = vis.all_whiteboards(update_timestamp=updated_at)

        # Save whiteboards to file
        check_dir(app.config.get("DATA_DIR") + "/figs/projects")

        with open(
            app.config.get("DATA_DIR") + "/figs/projects/projects.html", "w"
        ) as f:
            f.write(whiteboards["project_print"])

        with open(
            app.config.get("DATA_DIR") + "/figs/projects/project_screen.html", "w"
        ) as f:
            f.write(whiteboards["project_screen"])

        check_dir(app.config.get("DATA_DIR") + "/figs/people")

        with open(app.config.get("DATA_DIR") + "/figs/people/people.html", "w") as f:
            f.write(whiteboards["person_print"])

        with open(
            app.config.get("DATA_DIR") + "/figs/people/person_screen.html", "w"
        ) as f:
            f.write(whiteboards["person_screen"])

        print("Convert whiteboards to pdf...")
        # convert print version html to pdf
        cmd = "bash {home_dir}/scripts/whiteboard_to_pdf.sh".format(
            home_dir=app.config.get("HOME_DIR")
        )
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True)

        if result.returncode != 0:
            raise ValueError(
                "whiteboard_to_pdf.sh returned with code " + str(result.returncode)
            )

        # Generate & save demand vs capacity plot
        print("Demand vs capacity...")
        capacity_fig = vis.plot_demand_vs_capacity()
        capacity_fig.tight_layout()
        capacity_fig.savefig(
            app.config.get("DATA_DIR") + "/figs/demand_vs_capacity.png", dpi=300
        )
        plt.close("all")

        with open(
            app.config.get("DATA_DIR") + "/figs/demand_vs_capacity.html", "w"
        ) as f:
            f.write(
                """<!DOCTYPE html>
                <html>
                    <head>
                        <title>Index</title>
                    </head>
                    <body>
                        <img src="demand_vs_capacity.png" alt="demand_vs_capacity">
                    </body>
                </html>"""
            )

        print("Make zip file...")
        # create zip of print version whiteboard files
        with zipfile.ZipFile(
            app.config.get("DATA_DIR") + "/whiteboard.zip", "w"
        ) as zipf:
            zipf.write(
                app.config.get("DATA_DIR") + "/figs/projects/project_screen.html",
                "projects.html",
            )
            zipf.write(
                app.config.get("DATA_DIR") + "/figs/people/person_screen.html",
                "people.html",
            )
            zipf.write(
                app.config.get("DATA_DIR") + "/figs/projects/projects.pdf",
                "projects.pdf",
            )
            zipf.write(
                app.config.get("DATA_DIR") + "/figs/people/people.pdf", "people.pdf"
            )
            zipf.write(
                app.config.get("DATA_DIR") + "/figs/demand_vs_capacity.png",
                "demand_vs_capacity.png",
            )

        # save update time to file if everything was successful
        with open(app.config.get("DATA_DIR") + "/.last_update", "w") as f:
            f.write(updated_at)

        return render_template("update.html", updated_at=updated_at)

    except:
        return traceback.format_exc()


@app.route("/projects")
def projects(update_db=False):
    """Get the projects whiteboard.

    Returns:
        str -- HTML representation of the projects whiteboard.
    """
    try:
        if not os.path.isfile(
            app.config.get("DATA_DIR") + "/figs/projects/project_screen.html"
        ):
            update(update_db=update_db)

        with open(
            app.config.get("DATA_DIR") + "/figs/projects/project_screen.html", "r"
        ) as f:
            whiteboard = f.read()

        return whiteboard

    except:
        return traceback.format_exc()


@app.route("/people")
def people(update_db=False):
    """Get the people whiteboard

    Returns:
        str -- HTML representation of the people whiteboard.
    """
    try:
        if not os.path.isfile(
            app.config.get("DATA_DIR") + "/figs/people/person_screen.html"
        ):
            update(update_db=update_db)

        with open(
            app.config.get("DATA_DIR") + "/figs/people/person_screen.html", "r"
        ) as f:
            whiteboard = f.read()

        return whiteboard

    except:
        return traceback.format_exc()


@app.route("/preferences")
def preferences(update_db=False):
    """Get the preferences table

    Returns:
        str -- HTML representation of the preferences table.
    """
    try:
        if not os.path.isfile(
            app.config.get("DATA_DIR") + "/figs/preferences/preferences.html"
        ):
            update(update_db=update_db)

        with open(
            app.config.get("DATA_DIR") + "/figs/preferences/preferences.html", "r"
        ) as f:
            whiteboard = f.read()

        return whiteboard

    except:
        return traceback.format_exc()


@app.route("/download")
def download():
    """Get a zip of whiteboard files.

    Returns:
        Flask response -- Flask representation of zip file to deliver.
    """
    try:
        response = send_from_directory(
            app.config.get("DATA_DIR"), "whiteboard.zip", as_attachment=True
        )

        # change headers to stop browser from delivering cached version
        response.headers["Last-Modified"] = datetime.now()
        response.headers[
            "Cache-Control"
        ] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"

        return response

    except:
        return traceback.format_exc()


@app.route("/demand_vs_capacity")
def demand_vs_capacity():
    """Display demand vs capacity plot.

    Returns:
        Flask response -- Flask representation of zip file to deliver.
    """
    try:
        path = app.config.get("DATA_DIR") + "/figs/demand_vs_capacity.png"
        return send_file(path)

    except:
        return traceback.format_exc()


if __name__ == "__main__":
    # set home directory
    try:
        app.config["HOME_DIR"] = sys.argv[1]
    except:
        raise ValueError(
            "app.py must be passed path to home directory as first argument."
        )

    app.config["DATA_DIR"] = app.config.get("HOME_DIR") + "/data"

    # set working directory
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # run app
    app.run(host="0.0.0.0", port=int("8000"))
