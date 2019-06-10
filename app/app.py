from flask import Flask, send_from_directory

from wimbledon.vis.Visualise import Visualise
from wimbledon.api.DataUpdater import update_to_csv

import os
import zipfile
import traceback
import subprocess

DATA_DIR = '/WimbledonPlanner/data'

# set working directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# create app
app = Flask(__name__)


@app.route('/')
def home():
    return """
    WimbledonPlanner: Hut23 Project Planning<br>
    Browse to:<br>
     * /projects for projects whiteboard<br>
     * /people for people whiteboard<br>
     * /update to update the whiteboards (slow!)<br>
     * /download to download the whiteboard visualisations
    """


@app.route('/update')
def update():
    try:
        update_to_csv(DATA_DIR, run_forecast=True, run_harvest=False)

        vis = Visualise(init_harvest=False, data_source='csv', data_dir='../data')

        whiteboard = vis.whiteboard('project')
        with open(DATA_DIR+'/figs/projects/projects.html', 'w') as f:
            f.write(whiteboard)

        whiteboard = vis.whiteboard('person')
        with open(DATA_DIR+'/figs/people/people.html', 'w') as f:
            f.write(whiteboard)

        return 'DATA UPDATED!'

    except:
        return traceback.format_exc()


@app.route('/projects')
def projects():
    try:
        if not os.path.isfile(DATA_DIR+'/figs/projects/projects.html'):
            update()

        with open(DATA_DIR+'/figs/projects/projects.html', 'r') as f:
            whiteboard = f.read()

        return whiteboard

    except:
        return traceback.format_exc()


@app.route('/download')
def download():
    subprocess.call(["sh", "../scripts/whiteboard_to_pdf.sh"])

    with zipfile.ZipFile(DATA_DIR+'/whiteboard.zip', 'w') as zipf:
        zipf.write(DATA_DIR+'/figs/projects/projects.html', 'projects.html')
        zipf.write(DATA_DIR+'/figs/people/people.html', 'people.html')
        zipf.write(DATA_DIR + '/figs/projects/projects.pdf', 'projects.pdf')
        zipf.write(DATA_DIR + '/figs/people/people.pdf', 'people.pdf')

    return send_from_directory(DATA_DIR, 'whiteboard.zip')


@app.route('/people')
def people():
    try:
        if not os.path.isfile(DATA_DIR+'/figs/people/people.html'):
            update()

        with open(DATA_DIR+'/figs/people/people.html', 'r') as f:
            whiteboard = f.read()

        return whiteboard

    except:
        return traceback.format_exc()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int("8000"))
