import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import plotly.figure_factory as ff

app = dash.Dash(__name__)

# df = pd.read_csv('../data/forecast/assignments.csv')
df = pd.read_csv('../data/forecast/projects.csv')

df['start_date'] = pd.to_datetime(df['start_date'])
df['end_date'] = pd.to_datetime(df['end_date'])

start_date = pd.Timestamp('2019-01-01')
mask = df['start_date'] > start_date
df = df[mask]

df = df[['name', 'start_date', 'end_date']].rename(columns={'name': 'Task',
                                                            'start_date': 'Start',
                                                            'end_date': 'Finish'})

fig = ff.create_gantt(df.dropna().reset_index(), colors=['#333F44', '#93e4c1'],
                      bar_width=0.35, showgrid_x=True, showgrid_y=True,height=1500,width=1000)

app.layout = html.Div([
    dcc.Graph(
        id='fig-gantt',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
