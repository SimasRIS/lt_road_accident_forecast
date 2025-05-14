import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# COMMON DATA
EVENTS_CSV = '../data/processed/cleaned_events.csv'
PARTICIPANTS_CSV = '../data/processed/cleaned_participants.csv'

"""
Shows how the number of traffic accidents changed each year from 2013 to 2023.
Uses a Simple Moving Average (SMA) to predict the number of accidents up to 2026.
The results are displayed in a chart.
"""
def forecast_accidents_sma():
    events_df = pd.read_csv(EVENTS_CSV, usecols=['registrokodas', 'metai'])
    events_per_year = events_df[events_df['metai'].between(2013, 2023)]
    events_summary = events_per_year.groupby('metai').size().reset_index(name='accident_count')
    events_summary['SMA'] = events_summary['accident_count'].rolling(window=3, min_periods=1).mean()

    last_sma = events_summary['SMA'].iloc[-1]
    future_events = pd.DataFrame({
        'metai': [2024, 2025, 2026],
        'accident_count': [np.nan] * 3,
        'SMA': [last_sma] * 3
    })

    full_events = pd.concat([events_summary, future_events], ignore_index=True)

    plt.figure(figsize=(10, 6))
    plt.plot(full_events['metai'], full_events['accident_count'], 'o-', label='Historical data', color='darkblue')
    plt.plot(full_events['metai'], full_events['SMA'], 's--', label='Moving average / forecast', color='orange')
    plt.title('Forecast of Traffic Accidents in Lithuania (2013–2026)')
    plt.xlabel('Year')
    plt.ylabel('Number of Accidents')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.show()

"""
Analyzes data on people who died in traffic accidents:
- how many men and women died,
- their age groups,
- what type of accidents they were involved in (e.g., collisions, pedestrian accidents).
Uses data from 2017 to 2023.
"""
def analyze_deaths_by_gender_age_type():
    events_df = pd.read_csv(EVENTS_CSV)
    participants_df = pd.read_csv(PARTICIPANTS_CSV)

    # Gender
    deaths_df = participants_df[participants_df['bukle'] == 'Žuvo']
    merged_df = deaths_df.merge(events_df[['registrokodas', 'metai']], on='registrokodas')
    relevant_deaths = merged_df[merged_df['metai'].between(2017, 2023)]
    deaths_by_gender = relevant_deaths['lytis'].value_counts().reset_index()
    deaths_by_gender.columns = ['Gender', 'Death count']

    plt.figure(figsize=(6, 4))
    plt.bar(deaths_by_gender['Gender'], deaths_by_gender['Death count'])
    plt.title('Deaths by Gender (2017–2023)')
    plt.tight_layout()
    plt.show()

    # Age
    relevant_deaths = relevant_deaths[relevant_deaths['amzius'] != 'Uknown']
    relevant_deaths['amzius'] = relevant_deaths['amzius'].astype(float)
    bins = [0, 18, 30, 45, 60, 75, 100]
    labels = ['0–17', '18–29', '30–44', '45–59', '60–74', '75+']
    relevant_deaths['age_group'] = pd.cut(relevant_deaths['amzius'], bins=bins, labels=labels, right=False)

    deaths_by_age_group = relevant_deaths['age_group'].value_counts().sort_index().reset_index()
    deaths_by_age_group.columns = ['Age group', 'Death count']

    plt.figure(figsize=(6, 4))
    plt.bar(deaths_by_age_group['Age group'], deaths_by_age_group['Death count'])
    plt.title('Deaths by Age Group (2017–2023)')
    plt.tight_layout()
    plt.show()

    # Accident type
    merged_rusis = deaths_df.merge(events_df[['registrokodas', 'metai', 'rusis']], on='registrokodas')
    relevant_rusis = merged_rusis[merged_rusis['metai'].between(2017, 2023)]
    deaths_by_type = relevant_rusis['rusis'].value_counts().reset_index()
    deaths_by_type.columns = ['Accident type', 'Death count']

    plt.figure(figsize=(8, 6))
    plt.barh(deaths_by_type['Accident type'], deaths_by_type['Death count'])
    plt.title('Deaths by Type of Accident (2017–2023)')
    plt.tight_layout()
    plt.show()

"""
Shows on which days of the week most fatal accidents happened.
Uses data from 2017 to 2023. Results are displayed in a bar chart.
"""
def analyze_deaths_by_weekday():
    events_df = pd.read_csv(EVENTS_CSV)
    participants_df = pd.read_csv(PARTICIPANTS_CSV)
    deaths_df = participants_df[participants_df['bukle'] == 'Žuvo']
    merged_df = deaths_df.merge(events_df[['registrokodas', 'dataLaikas', 'metai']], on='registrokodas')
    filtered_df = merged_df[merged_df['metai'].between(2017, 2023)]
    filtered_df['dataLaikas'] = pd.to_datetime(filtered_df['dataLaikas'], errors='coerce')
    filtered_df['weekday'] = filtered_df['dataLaikas'].dt.dayofweek
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    filtered_df['weekday'] = filtered_df['weekday'].map(dict(zip(range(7), weekdays)))
    deaths_by_day = filtered_df['weekday'].value_counts().reindex(weekdays).reset_index()
    deaths_by_day.columns = ['Weekday', 'Death count']

    plt.figure(figsize=(8, 5))
    plt.bar(deaths_by_day['Weekday'], deaths_by_day['Death count'])
    plt.title('Deaths by Weekday (2017–2023)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

"""
Creates an interactive chart showing how many people died in traffic accidents from 2013 to 2023.
Uses a moving average (SMA) to forecast deaths up to 2026.
Uses the Plotly library for interactive visualization.
"""
def plotly_death_forecast():
    events_df = pd.read_csv(EVENTS_CSV, usecols=['registrokodas', 'metai'])
    participants_df = pd.read_csv(PARTICIPANTS_CSV)
    deaths_df = participants_df[participants_df['bukle'] == 'Žuvo']
    merged_df = deaths_df.merge(events_df, on='registrokodas')
    yearly_deaths = merged_df[merged_df['metai'].between(2013, 2023)]
    deaths_per_year = yearly_deaths.groupby('metai').size().reset_index(name='Death count')
    deaths_per_year['SMA'] = deaths_per_year['Death count'].rolling(window=3, min_periods=1).mean()
    last_sma = deaths_per_year['SMA'].iloc[-1]
    future_years = pd.DataFrame({
        'metai': [2024, 2025, 2026],
        'Death count': [np.nan] * 3,
        'SMA': [last_sma] * 3
    })
    full_data = pd.concat([deaths_per_year, future_years], ignore_index=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=full_data['metai'], y=full_data['Death count'],
                             mode='lines+markers', name='Historical data', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=full_data['metai'], y=full_data['SMA'],
                             mode='lines+markers', name='Forecast', line=dict(color='green', dash='dash')))
    fig.update_layout(title='Traffic Deaths Forecast (2013–2026)',
                      xaxis_title='Year', yaxis_title='Death count',
                      template='plotly_white', hovermode='x unified')
    fig.show()

"""
Shows how traffic accidents were distributed across months from 2017 to 2023.
Helps identify seasonal trends or months with more frequent incidents.
"""
def accidents_by_month():
    df = pd.read_csv(EVENTS_CSV)
    df_filtered = df[(df['metai'] >= 2017) & (df['metai'] <= 2023)]
    monthly_counts = df_filtered.groupby(['menuo', 'metai']).size().unstack()
    monthly_counts.plot(kind='bar', figsize=(14, 6), colormap='tab10')
    plt.title('Traffic Accidents by Month (2017–2023)')
    plt.xlabel('Month')
    plt.ylabel('Number of Accidents')
    plt.xticks(ticks=range(12), labels=[str(m) for m in range(1, 13)], rotation=0)
    plt.legend(title='Year', loc='center left', bbox_to_anchor=(1.0, 0.5))
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    forecast_accidents_sma()
    analyze_deaths_by_gender_age_type()
    analyze_deaths_by_weekday()
    plotly_death_forecast()
    accidents_by_month()

