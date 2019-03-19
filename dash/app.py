import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output

import plotly.graph_objs as go
import plotly.figure_factory as ff

import pandas as pd
from datetime import datetime as dt

app = dash.Dash(__name__)

# df = pd.read_csv('../data/forecast/assignments.csv')
df = pd.read_csv('../data/forecast/projects.csv')

df['start_date'] = pd.to_datetime(df['start_date'])
df['end_date'] = pd.to_datetime(df['end_date'])

#start_date = pd.Timestamp('2019-01-01')
#mask = df['start_date'] > start_date
#df = df[mask]

df = df[['name', 'start_date', 'end_date']].rename(columns={'name': 'Task',
                                                            'start_date': 'Start',
                                                            'end_date': 'Finish'})

# <br> adds a new line
#df['Task'].replace('Urban systems resilience', 'Urban systems<br>resilience', inplace=True)

#fig = ff.create_gantt(df.dropna().reset_index(), colors=['#333F44', '#93e4c1'], title='',
#                      bar_width=0.35, showgrid_x=True, showgrid_y=True, height=800, width=1000)


# setting larger left margin helps cropped name issue
#fig['layout'].update(margin=dict(l=220))


app.layout = html.Div([
    dcc.DatePickerRange(
        id='date-picker',
        min_date_allowed=dt(2018, 1, 1),
        max_date_allowed=dt(2022, 1, 1),
        initial_visible_month=dt.today(),
        start_date=dt(2019,1,1),
        end_date=dt(2019, 12, 31)
    ),

    dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in df.columns],
        style_table={
            'maxWidth': '600',
            'maxHeight': '600',
            'overflowY': 'scroll'
        },
        style_cell={'textAlign': 'center'},
        style_cell_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            },

            {
                'if': {'column_id': 'Task'},
                'textAlign': 'left'
            }
        ],
        style_as_list_view=True,
        style_header={
            'backgroundColor': 'blanchedalmond',
            'fontWeight': 'bold',
        },
        sorting=True
    ),

    dcc.Graph(
        id='fig-gantt',
    )
])


@app.callback(
    Output('fig-gantt', 'figure'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')])
def update_figure(start_date, end_date):
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    is_active = (df['Start'] <= start_date) & (df['Finish'] >= start_date)
    will_be_active = (df['Start'] >= start_date) & (df['Start'] <= end_date)
    mask = is_active | will_be_active
    filtered_df = df[mask]

    fig = ff.create_gantt(filtered_df.dropna().reset_index(), colors=['#333F44', '#93e4c1'], title='',
                          bar_width=0.35, showgrid_x=True, showgrid_y=True, height=800, width=1000)

    # setting larger left margin helps cropped name issue
    fig['layout'].update(margin=dict(l=220))
                         #xaxis=dict(range(start_date,end_date)))
    return fig


@app.callback(
    Output('table', 'data'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')])
def update_table(start_date, end_date):
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    is_active = (df['Start'] <= start_date) & (df['Finish'] >= start_date)
    will_be_active = (df['Start'] >= start_date) & (df['Start'] <= end_date)
    mask = is_active | will_be_active
    filtered_df = df[mask]
    data = filtered_df.dropna().reset_index().to_dict("rows")

    return data


if __name__ == '__main__':
    app.run_server(debug=True)
