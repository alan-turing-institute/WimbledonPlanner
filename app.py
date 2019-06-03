from flask import Flask

#from wimbledon.vis.Visualise import Visualise

app = Flask(__name__)


@app.route('/')
def hello_world():

    #vis = Visualise(init_harvest=False)

    #whiteboard = vis.whiteboard('project')

    try:
        import wimbledon
        return "SUCCESS!! "+wimbledon.__name__
    except ModuleNotFoundError:
        return '!!!!!! WIMBLEDON NOT FOUND !!!!!!!'

