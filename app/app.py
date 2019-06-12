from flask import Flask, send_from_directory

from wimbledon.vis.Visualise import Visualise
from wimbledon.api.DataUpdater import update_to_csv

import os
import zipfile
import traceback
import subprocess

from datetime import datetime

HOME_DIR = '/WimbledonPlanner'
HOME_DIR = '..'
DATA_DIR = HOME_DIR + '/data'

# set working directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# create app
app = Flask(__name__)


def check_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


@app.route('/')
def home():
    if os.path.isfile(DATA_DIR + '/.last_update'):
        with open(DATA_DIR + '/.last_update', 'r') as f:
            updated_at = f.read()
    else:
        updated_at = 'Never'

    return """
    WimbledonPlanner: Hut23 Project Planning<br>
    Last Updated: {updated_at}<br><br>
    Browse to:<br>
     * /projects for projects whiteboard<br>
     * /people for people whiteboard<br>
     * /update to update the whiteboards (slow!)<br>
     * /download to download the whiteboard visualisations     
    """.format(updated_at=updated_at)


@app.route('/update')
def update():
    try:
        update_to_csv(DATA_DIR, run_forecast=True, run_harvest=False)

        vis = Visualise(init_harvest=False, data_source='csv', data_dir='../data')

        updated_at = datetime.now().strftime('%d %b %Y, %H:%M')

        whiteboard = vis.whiteboard('project', update_timestamp=updated_at)
        check_dir(DATA_DIR+'/figs/projects')
        with open(DATA_DIR+'/figs/projects/projects.html', 'w') as f:
            f.write(whiteboard)

        whiteboard = vis.whiteboard('person', update_timestamp=updated_at)
        check_dir(DATA_DIR + '/figs/people')
        with open(DATA_DIR+'/figs/people/people.html', 'w') as f:
            f.write(whiteboard)

        with open(DATA_DIR+'/.last_update', 'w') as f:
            f.write(updated_at)

        return 'DATA UPDATED! ' + updated_at

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


@app.route('/download')
def download():
    try:
        cmd = 'sh {home_dir}/scripts/whiteboard_to_pdf.sh'.format(home_dir=HOME_DIR)
        subprocess.run(cmd, shell=True, check=True, capture_output=True)

        with zipfile.ZipFile(DATA_DIR+'/whiteboard.zip', 'w') as zipf:
            zipf.write(DATA_DIR+'/figs/projects/projects.html', 'projects.html')
            zipf.write(DATA_DIR+'/figs/people/people.html', 'people.html')
            zipf.write(DATA_DIR + '/figs/projects/projects.pdf', 'projects.pdf')
            zipf.write(DATA_DIR + '/figs/people/people.pdf', 'people.pdf')

        return send_from_directory(DATA_DIR, 'whiteboard.zip', as_attachment=True)

    except:
        return traceback.format_exc()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int("8000"))
