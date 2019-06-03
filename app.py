from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():

    #vis = Visualise(init_harvest=False)

    #whiteboard = vis.whiteboard('project')

    try:
        from wimbledon.vis.Visualise import Visualise
        return "SUCCESS!! "+Visualise.__name__
    except Exception as e:
        return str(e)

