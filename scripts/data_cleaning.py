import pandas as pd
import os
from scripts.data_loading import load_all_jsons

"""
Cleans road accidents main data.
"""
def clean_events(df):
    selected_columns = [
        "registrokodas", "dataLaikas", "savivaldybe", "ivykioVieta",
        "rusis", "schema1", "schema2", "dangosBukle", "parosMetas",
        "kelioApsvietimas", "meteoSalygos", "neblaivusKaltininkai",
        "apsvaigeKaltininkai", "dalyviuSkaicius", "zuvusiuSkaicius",
        "zuvVaiku", "suzeistuSkaicius", "suzeistaVaiku", "ilguma",
        "platuma", "leistinasGreitis"
    ]
    df = df[selected_columns]
    df['dataLaikas'] = pd.to_datetime(df['dataLaikas'], format='%Y-%m-%d %H:%M')
    df['metai'] = df['dataLaikas'].dt.year
    df['menuo'] = df['dataLaikas'].dt.month
    df['diena'] = df['dataLaikas'].dt.day
    df['valanda'] = df['dataLaikas'].dt.hour
    df.fillna('Unknown', inplace=True)
    return df

"""
Cleans road accidents participants data.
"""
def clean_participants(df):
    participants = pd.json_normalize(
        df.to_dict(orient='records'),
        record_path='eismoDalyviai',
        meta=['registrokodas']
    )
    selected_participant_columns = [
        "dalyvisId", "registrokodas", "kategorija", "lytis", "amzius",
        "bukle", "busena", "girtumasPromilemis", "kaltininkas", "dalyvioBusena",
        "vairavimoStazas", "dalyvioKetPazeidimai"
    ]
    participants = participants[selected_participant_columns]
    participants.fillna('Unknown', inplace=True)
    return participants

if __name__ == "__main__":
    # Reads all JSON files
    folder = '../data/raw/'
    df = load_all_jsons(folder)

    # Cleaning data
    events_df = clean_events(df)
    participants_df = clean_participants(df)

    # Creating 'data/processed' dir if there is none
    os.makedirs('../data/processed/', exist_ok=True)

    # Saving to CSV
    events_df.to_csv('../data/processed/cleaned_events.csv', index=False, encoding='utf-8')
    participants_df.to_csv('../data/processed/cleaned_participants.csv', index=False, encoding='utf-8')

    print(f'Saved: {events_df.shape[0]} events and {participants_df.shape[0]} participants.')




