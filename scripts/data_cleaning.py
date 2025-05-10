import pandas as pd
import numpy as np
import os
from scripts.data_loading import load_all_jsons

# Paths to raw and processed data
RAW_DIR = "../data/raw/"
PROCESSED_DIR = "../data/processed/"

# Columns for events cleaning
EVENT_COLS = [
    "registrokodas", "dataLaikas", "savivaldybe", "ivykioVieta",
    "rusis", "schema1", "schema2", "dangosBukle", "parosMetas",
    "kelioApsvietimas", "meteoSalygos", "neblaivusKaltininkai",
    "apsvaigeKaltininkai", "dalyviuSkaicius", "zuvusiuSkaicius",
    "zuvVaiku", "suzeistuSkaicius", "suzeistaVaiku",
    "ilguma", "platuma", "leistinasGreitis"
]
NUMERIC_EVENT_COLS = [
    "dalyviuSkaicius", "zuvusiuSkaicius", "zuvVaiku",
    "suzeistuSkaicius", "suzeistaVaiku", "ilguma",
    "platuma", "leistinasGreitis"
]

# Columns for participants cleaning
PARTICIPANT_COLS = [
    "dalyvisId", "registrokodas", "kategorija", "lytis", "amzius",
    "bukle", "busena", "girtumasPromilemis", "kaltininkas",
    "dalyvioBusena", "vairavimoStazas", "dalyvioKetPazeidimai"
]
NUMERIC_PARTICIPANT_COLS = ["amzius", "girtumasPromilemis", "vairavimoStazas"]


def clean_events(df):
    # Keep only needed columns
    df = df[EVENT_COLS].copy()

    # Convert dataLaikas to datetime
    df['dataLaikas'] = pd.to_datetime(df['dataLaikas'], format='%Y-%m-%d %H:%M', errors='coerce')

    # Create date parts
    df['metai'] = df['dataLaikas'].dt.year
    df['menuo'] = df['dataLaikas'].dt.month
    df['diena'] = df['dataLaikas'].dt.day
    df['valanda'] = df['dataLaikas'].dt.hour

    # Fill missing categorical values with 'Unknown'
    for col in EVENT_COLS:
        if col not in NUMERIC_EVENT_COLS and col != 'dataLaikas':
            df[col] = df[col].fillna('Unknown')

    # Convert numeric columns to numbers, others become NaN
    for col in NUMERIC_EVENT_COLS:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def clean_participants(df):
    # Expand nested participant list
    parts = pd.json_normalize(
        df.to_dict('records'), record_path='eismoDalyviai', meta=['registrokodas']
    )

    # Keep only needed columns
    parts = parts[PARTICIPANT_COLS].copy()

    # Fill missing text columns with 'Unknown'
    for col in PARTICIPANT_COLS:
        if col not in NUMERIC_PARTICIPANT_COLS:
            parts[col] = parts[col].fillna('Unknown')

    # Convert numeric participant columns
    for col in NUMERIC_PARTICIPANT_COLS:
        parts[col] = pd.to_numeric(parts[col], errors='coerce')

    return parts


if __name__ == '__main__':
    # Load raw JSON data
    raw_df = load_all_jsons(RAW_DIR)

    # Clean data
    events_df = clean_events(raw_df)
    participants_df = clean_participants(raw_df)

    # Make sure processed directory exists
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Save cleaned CSVs
    events_df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_events.csv'), index=False, encoding='utf-8')
    participants_df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_participants.csv'), index=False, encoding='utf-8')

    print('Saved {} events and {} participants.'.format(len(events_df), len(participants_df)))
