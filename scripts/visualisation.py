import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def accidents_by_month(df: pd.DataFrame) -> go.Figure:
    """
    Shows total accidents per calendar month.
    """
    df2 = df.copy()
    df2['month'] = df2['date'].dt.to_period('M').dt.to_timestamp()
    monthly = df2.groupby('month').size().reset_index(name='count')
    fig = px.bar(monthly, x='month', y='count', title='Accidents by Month')
    fig.update_layout(xaxis_title='Month', yaxis_title='Number of Accidents')
    return fig


def forecast_accidents_sma(df: pd.DataFrame) -> go.Figure:
    """
    Forecast trend using 12-month simple moving average.
    """
    df2 = df.copy()
    df2['month'] = df2['date'].dt.to_period('M').dt.to_timestamp()
    monthly = df2.groupby('month').size().reset_index(name='count')
    monthly['sma12'] = monthly['count'].rolling(window=12, min_periods=1).mean()
    fig = px.line(monthly, x='month', y='sma12', markers=True, title='12-Month SMA of Accidents')
    fig.update_layout(xaxis_title='Month', yaxis_title='12-Month SMA')
    return fig


def plotly_death_forecast(df: pd.DataFrame) -> go.Figure:
    """
    Shows a forecast of fatalities trend via linear regression.
    """
    df2 = df.copy()
    df2['month'] = df2['date'].dt.to_period('M').dt.to_timestamp()
    fatalities = df2.groupby('month')['zuvusiuSkaicius'].sum().reset_index()
    # Linear trend line
    coef = np.polyfit(fatalities.index, fatalities['zuvusiuSkaicius'], 1)
    fatalities['trend'] = np.polyval(coef, fatalities.index)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fatalities['month'], y=fatalities['zuvusiuSkaicius'], mode='lines+markers', name='Fatalities'))
    fig.add_trace(go.Scatter(x=fatalities['month'], y=fatalities['trend'], mode='lines', name='Linear Trend'))
    fig.update_layout(title='Fatalities Trend Forecast', xaxis_title='Month', yaxis_title='Deaths')
    return fig


def analyze_deaths_by_gender_age_type(df: pd.DataFrame) -> go.Figure:
    """
    Pie chart of fatalities by gender.
    """
    df2 = df.copy()
    if 'lytis' in df2.columns:
        gender = df2.groupby('lytis')['zuvusiuSkaicius'].sum().reset_index()
        fig = px.pie(gender, names='lytis', values='zuvusiuSkaicius', title='Fatalities by Gender')
    else:
        fig = go.Figure()
        fig.update_layout(title='No gender data available')
    return fig


def analyze_deaths_by_weekday(df: pd.DataFrame) -> go.Figure:
    """
    Bar chart of fatalities by weekday.
    """
    df2 = df.copy()
    df2['weekday'] = df2['date'].dt.day_name()
    wk = df2.groupby('weekday')['zuvusiuSkaicius'].sum().reindex(
        ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    ).reset_index()
    fig = px.bar(wk, x='weekday', y='zuvusiuSkaicius', title='Fatalities by Weekday')
    fig.update_layout(
        xaxis_title='Weekday',
        yaxis_title='Deaths',
        xaxis={'categoryorder':'array','categoryarray':['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']}
    )
    return fig
