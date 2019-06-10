from flask import Flask, send_from_directory

from wimbledon.vis.Visualise import Visualise
from wimbledon.api.DataUpdater import update_to_csv

import os
import zipfile

# set working directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# create app
app = Flask(__name__)


@app.route('/')
def home():
    return 'HELLO WORLD!'


@app.route('/update')
def update():
    update_to_csv('../data', run_forecast=True, run_harvest=False)

    vis = Visualise(init_harvest=False, data_source='csv', data_dir='../data')

    whiteboard = vis.whiteboard('project')
    with open('../data/figs/projects/projects.html', 'w') as f:
        f.write(whiteboard)

    whiteboard = vis.whiteboard('person')
    with open('../data/figs/people/people.html', 'w') as f:
        f.write(whiteboard)

    return 'DATA UPDATED!'


@app.route('/projects')
def projects():

    with open('../data/figs/projects/projects.html', 'r') as f:
        whiteboard = f.read()

    return whiteboard


@app.route('/download')
def download():
    with zipfile.ZipFile('../data/whiteboard.zip', 'w') as zipf:
        zipf.write('../data/figs/projects/projects.html', 'projects.html')
        zipf.write('../data/figs/people/people.html', 'people.html')

    return send_from_directory('../data', 'whiteboard.zip')


@app.route('/people')
def people():

    with open('../data/figs/people/people.html', 'r') as f:
        whiteboard = f.read()

    return whiteboard


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int("8000"))
