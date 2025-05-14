import pandas as pd
from pyproj import Transformer
import dash
from dash import dcc, html, Output, Input
import plotly.express as px

# Data preparation
# load cleaned data
df = pd.read_csv('../data/processed/cleaned_events.csv')
# Filters data from 2013 to 2023
df = df[(df['metai'] >= 2013) & (df['metai'] <= 2023)]

# Converts coordinates from LKS92 (EPSG:3346) to WGS84 (EPSG:4326)
transformer = Transformer.from_crs('epsg:3346', 'epsg:4326', always_xy=True)
# Perfom coordinate conversation (swaping easting/nothong)
lon, lat = transformer.transform(df['platuma'].values, df['ilguma'].values)
df['lon'] = lon
df['lat'] = lat

# Extract sorted lists of unique event types and years
categories = sorted(df['rusis'].unique().tolist())
years = sorted(int(y) for y in df['metai'].unique().tolist())

# Dash Application configuration
app = dash.Dash(__name__)
app.title = "LTU Traffic Incident Map"

app.layout = html.Div([
    html.H1("Distribution of traffic accidents in Lithuania 2013–2023"),
    html.Div([
        html.Label("Event type:"),
        dcc.Dropdown(
            id='category-dropdown',
            options=[{'label': cat, 'value': cat} for cat in categories],
            value=categories[0],
            clearable=False,
            style={'width': '300px'}
        )
    ], style={'display': 'inline-block', 'marginRight': '20px'}),
    html.Div([
        html.Label("Years:"),
        dcc.Slider(
            id='year-slider',
            min=years[0],
            max=years[-1],
            value=years[0],
            marks={year: str(year) for year in years},
            step=None
        )
    ], style={'display': 'inline-block', 'width': '60%'}),
    dcc.Graph(id='map-graph', config={'displayModeBar': True})
], style={'padding': '20px'})

# Map Figure Creation Function
def make_scatter_map(category: str, year: int):
    subset = df[(df['rusis'] == category) & (df['metai'] == year)]
    # If no data, return an empty figure
    if subset.empty:
        fig = px.scatter_map(lat=[], lon=[])
    else:
        fig = px.scatter_map(
            subset,
            lat='lat',
            lon='lon',
            hover_data={'metai': True, 'rusis': True}
        )
    # General layout settings
    layout_kwargs = {
        'mapbox_style': 'open-street-map',
        'mapbox_center': {'lat': 55.0, 'lon': 25.0},
        'mapbox_zoom': 6,
        'margin': dict(l=0, r=0, t=0, b=0)
    }

    fig.update_layout(**layout_kwargs)
    # If points exist, adjust marker styling
    if not subset.empty:
        fig.update_traces(marker=dict(size=6, opacity=0.7))
    return fig

# Map Update Callback
@app.callback(
    Output('map-graph', 'figure'),
    Input('category-dropdown', 'value'),
    Input('year-slider', 'value')
)
def update_map(category, year):
    return make_scatter_map(category, year)

# Run
if __name__ == '__main__':
    app.run(debug=True)