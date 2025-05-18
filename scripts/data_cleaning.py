import pandas as pd
import os
from dotenv import load_dotenv
import psycopg2
from scripts.data_loading import load_all_jsons

load_dotenv()

# PostgreSQL connection details
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = os.getenv('PG_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')

# Directory constants
RAW_DATA_DIR = '../data/raw/'
PROCESSED_DIR = '../data/processed/'
os.makedirs(PROCESSED_DIR, exist_ok=True)

def clean_events(df):
    selected_columns = [
        "registrokodas", "dataLaikas", "savivaldybe", "ivykioVieta",
        "rusis", "schema1", "schema2", "dangosBukle", "parosMetas",
        "kelioApsvietimas", "meteoSalygos", "neblaivusKaltininkai",
        "apsvaigeKaltininkai", "dalyviuSkaicius", "zuvusiuSkaicius",
        "zuvVaiku", "suzeistuSkaicius", "suzeistaVaiku", "ilguma",
        "platuma", "leistinasGreitis"
    ]
    df = df[selected_columns].copy()

    # Date and time
    df['dataLaikas'] = pd.to_datetime(df['dataLaikas'], format='%Y-%m-%d %H:%M')
    df['metai'] = df['dataLaikas'].dt.year
    df['menuo'] = df['dataLaikas'].dt.month
    df['diena'] = df['dataLaikas'].dt.day
    df['valanda'] = df['dataLaikas'].dt.hour

    # Convert "Taip"/"Ne" to numeric
    df['neblaivusKaltininkai'] = df['neblaivusKaltininkai'].map({'Taip': 1, 'Ne': 0}).fillna(0)
    df['apsvaigeKaltininkai'] = df['apsvaigeKaltininkai'].map({'Taip': 1, 'Ne': 0}).fillna(0)

    # Fill missing values
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col].fillna('Unknown', inplace=True)
        else:
            df[col].fillna(0, inplace=True)

    return df

def clean_participants(df):
    participants = pd.json_normalize(
        df.to_dict(orient='records'),
        record_path='eismoDalyviai',
        meta=['registrokodas']
    )

    selected_columns = [
        "dalyvisId", "registrokodas", "kategorija", "lytis", "amzius",
        "bukle", "busena", "girtumasPromilemis", "kaltininkas", "dalyvioBusena",
        "vairavimoStazas", "dalyvioKetPazeidimai"
    ]
    participants = participants[selected_columns].copy()

    # Convert 'kaltininkas' to boolean
    participants['kaltininkas'] = participants['kaltininkas'].astype(str).str.lower().map({
        'taip': True,
        'ne': False
    }).fillna(False)

    # Fill missing values
    for col in participants.columns:
        if participants[col].dtype == 'object':
            participants[col].fillna('Unknown', inplace=True)
        else:
            participants[col].fillna(0, inplace=True)

    return participants

def save_to_db(events_df, participants_df):
    with psycopg2.connect(
        dbname=DB_NAME,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT
    ) as conn:
        with conn.cursor() as cursor:
            events_df = events_df.drop_duplicates(subset='registrokodas')

            success, fail = 0, 0
            for _, row in events_df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO events VALUES (
                            %(registrokodas)s, %(dataLaikas)s, %(savivaldybe)s, %(ivykioVieta)s,
                            %(rusis)s, %(schema1)s, %(schema2)s, %(dangosBukle)s, %(parosMetas)s,
                            %(kelioApsvietimas)s, %(meteoSalygos)s, %(neblaivusKaltininkai)s,
                            %(apsvaigeKaltininkai)s, %(dalyviuSkaicius)s, %(zuvusiuSkaicius)s,
                            %(zuvVaiku)s, %(suzeistuSkaicius)s, %(suzeistaVaiku)s, %(ilguma)s,
                            %(platuma)s, %(leistinasGreitis)s, %(metai)s, %(menuo)s,
                            %(diena)s, %(valanda)s
                        )
                        ON CONFLICT (registrokodas) DO NOTHING;
                    """, row.to_dict())
                    success += 1
                except Exception as e:
                    fail += 1
                    print(f"Error inserting into events: {e}")
                    print(row.to_dict())
                    conn.rollback()

            print(f"Total inserted into events: {success}, errors: {fail}")

            cursor.execute("SELECT registrokodas FROM events;")
            existing_codes = set(code[0] for code in cursor.fetchall())

            before = len(participants_df)
            participants_df = participants_df[participants_df['registrokodas'].isin(existing_codes)]
            print(f"Filtered participants: {len(participants_df)} out of {before}")

            success, fail = 0, 0
            for _, row in participants_df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO participants (
                            dalyvisId, registrokodas, kategorija, lytis, amzius, bukle, busena,
                            girtumasPromilemis, kaltininkas, dalyvioBusena, vairavimoStazas, dalyvioKetPazeidimai
                        ) VALUES (
                            %(dalyvisId)s, %(registrokodas)s, %(kategorija)s, %(lytis)s, %(amzius)s, %(bukle)s, %(busena)s,
                            %(girtumasPromilemis)s, %(kaltininkas)s, %(dalyvioBusena)s, %(vairavimoStazas)s, %(dalyvioKetPazeidimai)s
                        );
                    """, row.to_dict())
                    success += 1
                except Exception as e:
                    fail += 1
                    print(f"Error inserting into participants: {e}")
                    print(row.to_dict())
                    conn.rollback()

            print(f"Total inserted into participants: {success}, errors: {fail}")
            conn.commit()
            print("Data successfully written to the database.")

if __name__ == "__main__":
    print("Starting data import...")
    df = load_all_jsons(RAW_DATA_DIR)
    print(f"Total records loaded: {df.shape[0]}")

    events_df = clean_events(df)
    participants_df = clean_participants(df)

    events_df = events_df[(events_df['metai'] >= 2013) & (events_df['metai'] <= 2023)].copy()
    print(f"Events after year‐filter: {events_df.shape[0]}")

    valid_codes = set(events_df["registrokodas"])
    participants_df = participants_df[
        participants_df["registrokodas"].isin(valid_codes)
    ].copy()
    print(f"Participants after matching to filtered events: {participants_df.shape[0]}")

    events_df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_events.csv'), index=False, encoding='utf-8')
    participants_df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_participants.csv'), index=False, encoding='utf-8')

    save_to_db(events_df, participants_df)
    print(f'Saved: {events_df.shape[0]} events and {participants_df.shape[0]} participants.')
