import os
import pandas as pd
from pyproj import Transformer
import dash
from dash import dcc, html, Output, Input
import plotly.express as px

# --- Duomenų paruošimas ---
# 1. Nuskaitome eismo įvykių duomenis
df = pd.read_csv('../data/processed/cleaned_events.csv')
# 2. Filtruojame įrašus nuo 2013 iki 2023 metų
df = df[(df['metai'] >= 2013) & (df['metai'] <= 2023)]
# 3. Konvertuojame koordinates iš LKS92 (EPSG:3346) į WGS84 (EPSG:4326)
transformer = Transformer.from_crs('epsg:3346', 'epsg:4326', always_xy=True)
# Transform should take easting (X) then northing (Y) for LKS92
# Columns in CSV: 'platuma' holds easting, 'ilguma' holds northing, so swap
lon, lat = transformer.transform(df['platuma'].values, df['ilguma'].values)
df['lon'] = lon
df['lat'] = lat

# 4. Išskiriame unikalias kategorijas ir metus
categories = sorted(df['rusis'].unique().tolist())
years = sorted(int(y) for y in df['metai'].unique().tolist())

# --- Dash aplikacijos konfigūracija ---
app = dash.Dash(__name__)
app.title = "LT Eismo Įvykių Žemėlapis"

app.layout = html.Div([
    html.H1("Lietuvos eismo įvykių pasiskirstymas 2013–2023"),
    html.Div([
        html.Label("Įvykio rūšis:"),
        dcc.Dropdown(
            id='category-dropdown',
            options=[{'label': cat, 'value': cat} for cat in categories],
            value=categories[0],
            clearable=False,
            style={'width': '300px'}
        )
    ], style={'display': 'inline-block', 'marginRight': '20px'}),
    html.Div([
        html.Label("Metai:"),
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

# --- Funkcija žemėlapiui sukurti ---
def make_scatter_map(category: str, year: int):
    subset = df[(df['rusis'] == category) & (df['metai'] == year)]
    # Jei nėra duomenų, grąžiname tuščią figūrą
    if subset.empty:
        fig = px.scatter_map(lat=[], lon=[])
    else:
        fig = px.scatter_map(
            subset,
            lat='lat',
            lon='lon',
            hover_data={'metai': True, 'rusis': True}
        )
    # Bendras figūros konfigūracija
    layout_kwargs = {
        'mapbox_style': 'open-street-map',
        'mapbox_center': {'lat': 55.0, 'lon': 25.0},
        'mapbox_zoom': 6,
        'margin': dict(l=0, r=0, t=0, b=0)
    }

    fig.update_layout(**layout_kwargs)
    # Jei yra taškų, pakoreguojame marker parametrus
    if not subset.empty:
        fig.update_traces(marker=dict(size=6, opacity=0.7))
    return fig

# --- Callback atnaujinimui ---
@app.callback(
    Output('map-graph', 'figure'),
    Input('category-dropdown', 'value'),
    Input('year-slider', 'value')
)
def update_map(category, year):
    return make_scatter_map(category, year)

# --- Paleidimas ---
if __name__ == '__main__':
    app.run(debug=True)