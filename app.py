from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():

    #vis = Visualise(init_harvest=False)

    #whiteboard = vis.whiteboard('project')

    try:
        #from wimbledon.vis.Visualise import Visualise
        import forecast
        return "SUCCESS!! "+forecast.__name__
    except ModuleNotFoundError as e:
        return str(e)

