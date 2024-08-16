import dash
from dash import html, dcc, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import requests
import datetime
from flask_caching import Cache

# Define Layout of App
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server

# Initialize caching
cache = Cache(app.server, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 3600  # Cache for 1 hour
})

# Constants
TOP_N_COUNTRIES = 10
UPDATE_INTERVAL = 86400000 * 7  # 7 days in milliseconds

app.layout = html.Div([
    html.H1('COVID-19 Vaccine Coverage by Country', style={'textAlign': 'center'}),
    dcc.Interval(id='interval_db', interval=UPDATE_INTERVAL, n_intervals=0),
    html.Div(id='dashboard-content', children=[
        html.Div(id='mongo-datatable', className='col-12 col-md-6'),
        html.Div(id='bar-graph', className='col-12 col-md-6'),
    ], className='row'),
    html.Div(id='last-update-time'),
    html.Div(id='error-message', style={'color': 'red'})
], className='container')


@cache.memoize()
def fetch_and_process_data():
    try:
        r = requests.get("https://disease.sh/v3/covid-19/vaccine/coverage/countries?lastdays=1")
        r.raise_for_status()  # Raises an HTTPError for bad responses
        data = r.json()

        df = pd.DataFrame(data)
        df['latest_coverage'] = df['timeline'].apply(lambda x: list(x.values())[0] if x else None)
        df = df.dropna(subset=['latest_coverage'])  # Remove rows with no coverage data
        df = df.drop(columns=['timeline'])
        return df.sort_values(by='latest_coverage', ascending=False).head(TOP_N_COUNTRIES)
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error


@app.callback(
    Output('mongo-datatable', 'children'),
    Output('bar-graph', 'children'),
    Output('last-update-time', 'children'),
    Output('error-message', 'children'),
    Input('interval_db', 'n_intervals')
)
def update_dashboard(n_intervals):
    df = fetch_and_process_data()
    if df.empty:
        return html.Div(), html.Div(), "", "Error: Unable to fetch data. Please try again later."

    table = dash_table.DataTable(
        id='our-table',
        data=df.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
    )

    bar_fig = px.bar(df, x='country', y='latest_coverage',
                     title=f'Top {TOP_N_COUNTRIES} Countries by Vaccine Coverage')

    last_update = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    return table, dcc.Graph(figure=bar_fig), f"Last updated: {last_update}", ""


if __name__ == '__main__':
    app.run_server(debug=False)