import pandas as pd
from pyproj import Transformer
import plotly.express as px
import plotly.offline as pyo

def load_map_data(path: str) -> pd.DataFrame:
    """
    Reads cleaned_events.csv, filters years, converts coords to WGS84,
    and returns a DataFrame with latitude/longitude.
    """
    df = pd.read_csv(path, parse_dates=['dataLaikas'])
    # optional year filtering
    df = df[(df['metai'] >= 2013) & (df['metai'] <= 2023)]
    # convert from LKS92 (EPSG:3346) → WGS84
    transformer = Transformer.from_crs('epsg:3346', 'epsg:4326', always_xy=True)
    df['lon'], df['lat'] = transformer.transform(
        df['platuma'].values,
        df['ilguma'].values
    )
    return df

def make_scatter_map(
    df: pd.DataFrame,
    category: str = None,
    year: int = None
) -> px.scatter_mapbox:
    """
    Builds a Plotly scatter_mapbox figure, optionally filtered by rusis/year.
    """
    d = df.copy()
    if category:
        d = d[d['rusis'] == category]
    if year:
        d = d[d['metai'] == year]

    fig = px.scatter_mapbox(
        d,
        lat='lat',
        lon='lon',
        color='rusis',                 # use the actual column name
        hover_data=['savivaldybe', 'dataLaikas', 'rusis'],
        zoom=6,
        height=600
    )
    fig.update_layout(
        mapbox_style='open-street-map',
        margin={'l': 0, 'r': 0, 't': 0, 'b': 0}
    )
    return fig

def create_map_div(
    csv_path: str,
    category: str = None,
    year: int = None
) -> str:
    """
    Returns the HTML <div> for embedding the map.
    """
    df = load_map_data(csv_path)
    fig = make_scatter_map(df, category, year)
    return pyo.plot(fig, include_plotlyjs='cdn', output_type='div')
