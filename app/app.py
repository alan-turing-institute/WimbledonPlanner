from flask import Flask, send_from_directory

from wimbledon.vis.Visualise import Visualise
from wimbledon.api.DataUpdater import update_to_csv

import os
import zipfile
import traceback
import subprocess
import sys

from datetime import datetime

app = Flask(__name__)


def check_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


@app.route('/')
def home():
    if os.path.isfile(app.config.get('DATA_DIR') + '/.last_update'):
        with open(app.config.get('DATA_DIR') + '/.last_update', 'r') as f:
            updated_at = f.read()
    else:
        updated_at = 'Never'

    return """
    WimbledonPlanner: Hut23 Project Planning<br>
    Last Updated: {updated_at}<br><br>
    Browse to:<br>
     * <a href="/projects">/projects</a> for projects whiteboard<br>
     * <a href="/people">/people</a> for people whiteboard<br>
     * <a href="/update">/update</a> to update the whiteboards (slow!)<br>
     * <a href="/download">/download</a> to download the whiteboard visualisations     
    """.format(updated_at=updated_at)


@app.route('/update')
def update():
    try:
        update_to_csv(app.config.get('DATA_DIR'), run_forecast=True, run_harvest=False)

        vis = Visualise(init_harvest=False, data_source='csv', data_dir='../data')

        updated_at = datetime.now().strftime('%d %b %Y, %H:%M')

        whiteboard = vis.whiteboard('project', update_timestamp=updated_at)
        check_dir(app.config.get('DATA_DIR')+'/figs/projects')
        with open(app.config.get('DATA_DIR')+'/figs/projects/projects.html', 'w') as f:
            f.write(whiteboard)

        whiteboard = vis.whiteboard('person', update_timestamp=updated_at)
        check_dir(app.config.get('DATA_DIR') + '/figs/people')
        with open(app.config.get('DATA_DIR')+'/figs/people/people.html', 'w') as f:
            f.write(whiteboard)

        with open(app.config.get('DATA_DIR')+'/.last_update', 'w') as f:
            f.write(updated_at)

        return 'DATA UPDATED! ' + updated_at + '<br><a href="/">back to home</a>'

    except:
        return traceback.format_exc()


@app.route('/projects')
def projects():
    try:
        if not os.path.isfile(app.config.get('DATA_DIR')+'/figs/projects/projects.html'):
            update()

        with open(app.config.get('DATA_DIR')+'/figs/projects/projects.html', 'r') as f:
            whiteboard = f.read()

        return whiteboard

    except:
        return traceback.format_exc()


@app.route('/people')
def people():
    try:
        if not os.path.isfile(app.config.get('DATA_DIR')+'/figs/people/people.html'):
            update()

        with open(app.config.get('DATA_DIR')+'/figs/people/people.html', 'r') as f:
            whiteboard = f.read()

        return whiteboard

    except:
        return traceback.format_exc()


@app.route('/download')
def download():

    try:
        cmd = 'bash {home_dir}/scripts/whiteboard_to_pdf.sh'.format(home_dir=app.config.get('HOME_DIR'))
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True)

        if result.returncode is not 0:
            raise ValueError('whiteboard_to_pdf.sh returned with code '+str(result.returncode))

        with zipfile.ZipFile(app.config.get('DATA_DIR')+'/whiteboard.zip', 'w') as zipf:
            zipf.write(app.config.get('DATA_DIR')+'/figs/projects/projects.html', 'projects.html')
            zipf.write(app.config.get('DATA_DIR')+'/figs/people/people.html', 'people.html')
            zipf.write(app.config.get('DATA_DIR') + '/figs/projects/projects.pdf', 'projects.pdf')
            zipf.write(app.config.get('DATA_DIR') + '/figs/people/people.pdf', 'people.pdf')

        return send_from_directory(app.config.get('DATA_DIR'), 'whiteboard.zip', as_attachment=True)

    except:
        return traceback.format_exc()


if __name__ == "__main__":
    # set home directory
    try:
        app.config['HOME_DIR'] = sys.argv[1]
    except:
        raise ValueError('app.py must be passed path to home directory as first argument.')

    app.config['DATA_DIR'] = app.config.get('HOME_DIR') + '/data'

    # set working directory
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # get latest data
    update()

    # run app
    app.run(host="0.0.0.0", port=int("8000"))
