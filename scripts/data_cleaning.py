import pandas as pd
import os
import psycopg2
from scripts.data_loading import load_all_jsons

# PostgreSQL prisijungimo duomenys
PG_USER = 'postgres'
PG_PASSWORD = '323157822'
PG_HOST = 'localhost'
PG_PORT = 5432
DB_NAME = 'traffic_accidents'

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

    # Data ir laikas
    df['dataLaikas'] = pd.to_datetime(df['dataLaikas'], format='%Y-%m-%d %H:%M')
    df['metai'] = df['dataLaikas'].dt.year
    df['menuo'] = df['dataLaikas'].dt.month
    df['diena'] = df['dataLaikas'].dt.day
    df['valanda'] = df['dataLaikas'].dt.hour

    # Konvertuojam "Taip"/"Ne" į skaitmenis
    df['neblaivusKaltininkai'] = df['neblaivusKaltininkai'].map({'Taip': 1, 'Ne': 0}).fillna(0)
    df['apsvaigeKaltininkai'] = df['apsvaigeKaltininkai'].map({'Taip': 1, 'Ne': 0}).fillna(0)

    # Užpildom trūkstamas reikšmes
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col].fillna('Unknown', inplace=True)
        else:
            df[col].fillna(0, inplace=True)

    df.rename(columns={
        'dataLaikas': 'data_laikas',
        'ivykioVieta': 'ivykio_vieta',
        'dangosBukle': 'dangos_bukle',
        'parosMetas': 'paros_metas',
        'kelioApsvietimas': 'kelio_apsvietimas',
        'meteoSalygos': 'meteo_salygos',
        'neblaivusKaltininkai': 'neblaivus_kaltininkai',
        'apsvaigeKaltininkai': 'apsvaige_kaltininkai',
        'dalyviuSkaicius': 'dalyviu_skaicius',
        'zuvusiuSkaicius': 'zuvusiu_skaicius',
        'zuvVaiku': 'zuv_vaiku',
        'suzeistuSkaicius': 'suzeistu_skaicius',
        'suzeistaVaiku': 'suzeista_vaiku',
        'leistinasGreitis': 'leistinas_greitis'
    }, inplace=True)

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

    # Konvertuojam 'kaltininkas' į boolean
    participants['kaltininkas'] = participants['kaltininkas'].astype(str).str.lower().map({
        'taip': True,
        'ne': False
    }).fillna(False)

    for col in participants.columns:
        if participants[col].dtype == 'object':
            participants[col].fillna('Unknown', inplace=True)
        else:
            participants[col].fillna(0, inplace=True)

    participants.rename(columns={
        'dalyvisId': 'dalyvis_id',
        'girtumasPromilemis': 'girtumas_promilemis',
        'dalyvioBusena': 'dalyvio_busena',
        'vairavimoStazas': 'vairavimo_stazas',
        'dalyvioKetPazeidimai': 'dalyvio_ket_pazeidimai'
    }, inplace=True)

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
            # Pašalinam dublikatus
            events_df = events_df.drop_duplicates(subset='registrokodas')

            # Įrašom įvykius
            success, fail = 0, 0
            for _, row in events_df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO events VALUES (
                            %(registrokodas)s, %(data_laikas)s, %(savivaldybe)s, %(ivykio_vieta)s,
                            %(rusis)s, %(schema1)s, %(schema2)s, %(dangos_bukle)s, %(paros_metas)s,
                            %(kelio_apsvietimas)s, %(meteo_salygos)s, %(neblaivus_kaltininkai)s,
                            %(apsvaige_kaltininkai)s, %(dalyviu_skaicius)s, %(zuvusiu_skaicius)s,
                            %(zuv_vaiku)s, %(suzeistu_skaicius)s, %(suzeista_vaiku)s, %(ilguma)s,
                            %(platuma)s, %(leistinas_greitis)s, %(metai)s, %(menuo)s,
                            %(diena)s, %(valanda)s
                        )
                        ON CONFLICT (registrokodas) DO NOTHING;
                    """, row.to_dict())
                    success += 1
                except Exception as e:
                    fail += 1
                    print(f"Klaida įrašant į events: {e}")
                    print(row.to_dict())
                    conn.rollback()

            print(f"Iš viso įrašyta į events: {success}, klaidų: {fail}")

            # Gauti realiai įrašytus registrokodus
            cursor.execute("SELECT registrokodas FROM events;")
            existing_codes = set(code[0] for code in cursor.fetchall())

            # Filtruojam participants
            before = len(participants_df)
            participants_df = participants_df[participants_df['registrokodas'].isin(existing_codes)]
            print(f"Filtruota dalyvių: {len(participants_df)} iš {before}")

            success, fail = 0, 0
            for _, row in participants_df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO participants (
                            dalyvis_id, registrokodas, kategorija, lytis, amzius, bukle, busena,
                            girtumas_promilemis, kaltininkas, dalyvio_busena, vairavimo_stazas, dalyvio_ket_pazeidimai
                        ) VALUES (
                            %(dalyvis_id)s, %(registrokodas)s, %(kategorija)s, %(lytis)s, %(amzius)s, %(bukle)s, %(busena)s,
                            %(girtumas_promilemis)s, %(kaltininkas)s, %(dalyvio_busena)s, %(vairavimo_stazas)s, %(dalyvio_ket_pazeidimai)s
                        );
                    """, row.to_dict())
                    success += 1
                except Exception as e:
                    fail += 1
                    print(f"Klaida įrašant į participants: {e}")
                    print(row.to_dict())
                    conn.rollback()

            print(f"Iš viso įrašyta į participants: {success}, klaidų: {fail}")
            conn.commit()
            print("Duomenys sėkmingai įrašyti į duomenų bazę.")

if __name__ == "__main__":
    folder = '../data/raw/'
    df = load_all_jsons(folder)

    print(f"Iš viso įkeltų įrašų: {df.shape[0]}")

    events_df = clean_events(df)
    participants_df = clean_participants(df)

    os.makedirs('../data/processed/', exist_ok=True)
    events_df.to_csv('../data/processed/cleaned_events_df.csv', index=False, encoding='utf-8')
    participants_df.to_csv('../data/processed/cleaned_participants_df.csv', index=False, encoding='utf-8')

    save_to_db(events_df, participants_df)

    print(f'Saved: {events_df.shape[0]} events and {participants_df.shape[0]} participants.')
