import dash
from dash import html, dcc, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import requests

# Define Layout of App
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server
app.layout = html.Div([
    html.H1('COVID-19 Vaccine Coverage by Country', style={'textAlign': 'center'}),
    dcc.Interval(id='interval_db', interval=86400000 * 7, n_intervals=0),
    html.Div(id='dashboard-content', children=[
        html.Div(id='mongo-datatable', className='twelve columns'),
        html.Div(id='bar-graph', className='twelve columns'),
    ], className='row')
])


def fetch_data():
    r = requests.get("https://disease.sh/v3/covid-19/vaccine/coverage/countries?lastdays=1")
    data = r.json()

    # Transform the data into a DataFrame
    df = pd.DataFrame(data)

    # Extract the last day of vaccine coverage
    df['latest_coverage'] = df['timeline'].apply(lambda x: list(x.values())[0])

    # Drop the timeline column for display
    df = df.drop(columns=['timeline'])

    # Sort and take the top 10 countries by vaccine coverage
    df = df.sort_values(by='latest_coverage', ascending=False).head(10)

    return df


@app.callback(
    Output('mongo-datatable', 'children'),
    Output('bar-graph', 'children'),
    Input('interval_db', 'n_intervals')
)
def update_dashboard(n_intervals):
    df = fetch_data()

    table = dash_table.DataTable(
        id='our-table',
        data=df.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
    )

    bar_fig = px.bar(df, x='country', y='latest_coverage', title='Top 10 Countries by Vaccine Coverage')

    return table, dcc.Graph(figure=bar_fig)


if __name__ == '__main__':
    app.run_server(debug=False)
