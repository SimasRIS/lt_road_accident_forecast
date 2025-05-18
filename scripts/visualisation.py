import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import calendar

"""
Forecast the number of traffic accidents per year (2013–2026) using a 3-year simple moving average.
events_df: DataFrame containing at least a 'metai' column with year of each event.
"""
def forecast_accidents_sma(events_df: pd.DataFrame) -> go.Figure:

    df = events_df.copy()
    df = df[df['metai'].between(2013, 2023)]
    summary = df.groupby('metai').size().reset_index(name='accident_count')
    summary['SMA'] = summary['accident_count'].rolling(window=3, min_periods=1).mean()

    last_sma = summary['SMA'].iloc[-1]
    future = pd.DataFrame({
        'metai': [2024, 2025, 2026],
        'accident_count': [None, None, None],
        'SMA': [last_sma] * 3
    })
    full = pd.concat([summary, future], ignore_index=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=full['metai'], y=full['accident_count'],
        mode='lines+markers', name='Historical data'
    ))
    fig.add_trace(go.Scatter(
        x=full['metai'], y=full['SMA'],
        mode='lines+markers', name='Moving average / forecast',
        line=dict(dash='dash')
    ))
    fig.update_layout(
        title='Forecast of Traffic Accidents in Lithuania (2013–2026)',
        xaxis_title='Year', yaxis_title='Number of Accidents'
    )
    return fig

"""
Analyze fatalities by gender, age group, and accident type (2017–2023).
Returns a combined figure with three subplots.
"""
def analyze_deaths_by_gender_age_type(events_df: pd.DataFrame, participants_df: pd.DataFrame) -> go.Figure:

    # Prepare merged data
    deaths = participants_df[participants_df['bukle'] == 'Žuvo']
    merged = deaths.merge(
        events_df[['registrokodas', 'metai', 'rusis']],
        on='registrokodas', how='left'
    )
    period = merged[merged['metai'].between(2017, 2023)]

    # Gender breakdown
    gender_counts = period['lytis'].value_counts().reset_index()
    gender_counts.columns = ['Gender', 'Count']

    # Age groups
    period = period[period['amzius'].notna() & (period['amzius'] != 'Unknown')]
    period['amzius'] = period['amzius'].astype(float)
    bins = [0, 18, 30, 45, 60, 75, np.inf]
    labels = ['0–17', '18–29', '30–44', '45–59', '60–74', '75+']
    period['age_group'] = pd.cut(period['amzius'], bins=bins, labels=labels, right=False)
    age_counts = period['age_group'].value_counts().sort_index().reset_index()
    age_counts.columns = ['Age group', 'Count']

    # Accident type breakdown
    type_counts = period['rusis'].value_counts().reset_index()
    type_counts.columns = ['Accident type', 'Count']

    # Create subplots
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=3, subplot_titles=(
        'Deaths by Gender', 'Deaths by Age Group', 'Deaths by Accident Type'
    ))

    fig.add_trace(
        go.Bar(x=gender_counts['Gender'], y=gender_counts['Count'], name='Gender'),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=age_counts['Age group'], y=age_counts['Count'], name='Age Group'),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(x=type_counts['Accident type'], y=type_counts['Count'], name='Acc Type', orientation='h'),
        row=1, col=3
    )

    fig.update_layout(
        height=500,
        showlegend=False,
        title_text='Fatalities Analysis (2017–2023)'
    )
    return fig

"""
Analyze on which weekdays most fatal accidents occurred (2017–2023).
"""
def analyze_deaths_by_weekday(events_df: pd.DataFrame, participants_df: pd.DataFrame) -> go.Figure:

    deaths = participants_df[participants_df['bukle'] == 'Žuvo']
    merged = deaths.merge(
        events_df[['registrokodas', 'dataLaikas', 'metai']],
        on='registrokodas', how='left'
    )
    df = merged[merged['metai'].between(2017, 2023)].copy()
    df['dataLaikas'] = pd.to_datetime(df['dataLaikas'], errors='coerce')
    df['weekday'] = df['dataLaikas'].dt.day_name()
    order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    wd_counts = df['weekday'].value_counts().reindex(order).reset_index()
    wd_counts.columns = ['Weekday', 'Count']

    fig = px.bar(
        wd_counts, x='Weekday', y='Count',
        title='Fatal Accidents by Weekday (2017–2023)'
    )
    fig.update_layout(xaxis_title='Weekday', yaxis_title='Number of Fatalities')
    return fig

"""
Forecast fatalities per year using a 3-year SMA (2013–2026).
"""
def plotly_death_forecast(events_df: pd.DataFrame, participants_df: pd.DataFrame) -> go.Figure:

    deaths = participants_df[participants_df['bukle'] == 'Žuvo']
    merged = deaths.merge(events_df[['registrokodas', 'metai']], on='registrokodas')
    yearly = merged[merged['metai'].between(2013, 2023)]
    df_counts = yearly.groupby('metai').size().reset_index(name='Death count')
    df_counts['SMA'] = df_counts['Death count'].rolling(window=3, min_periods=1).mean()

    last_sma = df_counts['SMA'].iloc[-1]
    future = pd.DataFrame({
        'metai': [2024, 2025, 2026],
        'Death count': [None, None, None],
        'SMA': [last_sma] * 3
    })
    full = pd.concat([df_counts, future], ignore_index=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=full['metai'], y=full['Death count'], mode='lines+markers', name='Historical'))
    fig.add_trace(go.Scatter(x=full['metai'], y=full['SMA'], mode='lines+markers', name='Forecast', line=dict(dash='dash')))
    fig.update_layout(
        title='Traffic Deaths Forecast (2013–2026)',
        xaxis_title='Year', yaxis_title='Death Count'
    )
    return fig


def accidents_by_month(events_df: pd.DataFrame) -> go.Figure:

    # Filtering
    df = events_df.copy()
    df = df[df['metai'].between(2017, 2023)]

    # Getting month
    df['month'] = df['dataLaikas'].dt.month

    # Group ny month and years
    monthly = (
        df
        .groupby(['month', 'metai'])
        .size()
        .reset_index(name='count')
    )

    # Creating bar char
    month_order = list(range(1, 13))
    fig = px.bar(
        monthly,
        x='month',
        y='count',
        color='metai',
        barmode='group',
        category_orders={'month': month_order},
        labels={
            'month': 'Month',
            'count': 'Number of Accidents',
            'metai': 'Year'
        },
        title='Traffic accidents by month and year (2017–2023)'
    )

    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=month_order,
            ticktext=[calendar.month_abbr[m] for m in month_order]
        ),
        legend_title_text='Years'
    )

    return fig

