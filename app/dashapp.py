import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash_dangerously_set_inner_html

from datetime import datetime as dt
import pandas as pd

from wimbledon.vis.Visualise import Visualise


app = dash.Dash(__name__)

vis = Visualise(init_harvest=False, data_source='csv', data_dir='../data')

start_date = pd.datetime.now() - pd.Timedelta('30 days')
end_date = pd.datetime.now() + pd.Timedelta('365 days')

earliest = vis.fc.date_range.min()
latest = vis.fc.date_range.max()

#projects = vis.whiteboard('project', start_date=start_date, end_date=end_date)
#people = vis.whiteboard('person', start_date=start_date, end_date=end_date)

app.layout = html.Div([
    dcc.Tabs(id="tabs", children=[
        dcc.Tab(label='Config',
                children=[dcc.DatePickerRange(
                            id='date-picker',
                            min_date_allowed=earliest,
                            max_date_allowed=latest,
                            initial_visible_month=pd.datetime.now(),
                            start_date=start_date,
                            end_date=end_date,
                            display_format='D MMM YYYY'),
                          html.Div(id='output-container-date-picker'),
                          html.Button('Generate', id='button'),
                          html.Div(id='output-container-button')]),
        dcc.Tab(label='Projects',
                children=[html.Div(id='projects_whiteboard')]),
        dcc.Tab(label='People',
                children=[html.Div(id='people_whiteboard')])
    ]),
])


@app.callback(
    dash.dependencies.Output('output-container-date-picker', 'children'),
    [dash.dependencies.Input('date-picker', 'start_date'),
     dash.dependencies.Input('date-picker', 'end_date')])
def update_output(start_date, end_date):
    output = ''
    if start_date is not None:
        output = output + str(start_date)
    if end_date is not None:
        output = output + ' - ' + end_date
    if len(output) == 0:
        return 'Select a date to see it displayed here'
    else:
        return 'Selected date range: ' + output


@app.callback(
    [dash.dependencies.Output('output-container-button', 'children'),
     dash.dependencies.Output('projects_whiteboard', 'children'),
     dash.dependencies.Output('people_whiteboard', 'children')],
    [dash.dependencies.Input('button', 'n_clicks')],
    [dash.dependencies.State('date-picker', 'start_date'),
     dash.dependencies.State('date-picker', 'end_date')])
def update_button(n_clicks, start_date, end_date):
    if n_clicks is None:
        n_clicks = 0
    
    projects = vis.whiteboard('project', start_date=start_date, end_date=end_date)
    people = vis.whiteboard('person', start_date=start_date, end_date=end_date)

    button_str = '{} clicks, start {}, end {}'.format(n_clicks, start_date, end_date)
    projects_div = dash_dangerously_set_inner_html.DangerouslySetInnerHTML(projects)
    people_div = dash_dangerously_set_inner_html.DangerouslySetInnerHTML(people)

    return [button_str, projects_div, people_div]


if __name__ == '__main__':
    app.run_server(debug=True)
