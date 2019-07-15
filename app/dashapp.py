import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash_dangerously_set_inner_html

from datetime import datetime as dt


app = dash.Dash(__name__)

with open('../data/figs/projects/projects.html', 'r') as f:
    projects = f.read()

with open('../data/figs/people/people.html', 'r') as f:
    people = f.read()

app.layout = html.Div([
    dcc.Tabs(id="tabs", children=[
        dcc.Tab(label='Config',
                children=[dcc.DatePickerRange(
                            id='date-picker',
                            min_date_allowed=dt(2017, 1, 1),
                            max_date_allowed=dt(2023, 1, 1),
                            initial_visible_month=dt(2019, 7, 1),
                            start_date=dt(2019, 6, 1),
                            end_date=dt(2020, 7, 1)),
                          html.Div(id='output-container-date-picker')]),
        dcc.Tab(label='Projects',
                children=[html.Div([dash_dangerously_set_inner_html.DangerouslySetInnerHTML(projects)],
                                   id='projects_whiteboard')]),
        dcc.Tab(label='People',
                children=[html.Div([dash_dangerously_set_inner_html.DangerouslySetInnerHTML(people)],
                                   id='people_whiteboard')])
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
        return output


if __name__ == '__main__':
    app.run_server(debug=True)
