import psycopg2
from psycopg2 import sql

PG_USER = 'postgres'
PG_PASSWORD = '323157822'
PG_HOST = 'localhost'
PG_PORT = 5432
#NUSAKOME DUOMENU BAZES PAVADINIMA, STULPELIUS IR SUKURIAM PACIA LENTELE


DB_NAME = 'traffic_accidents'
TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS events (
        registrokodas TEXT PRIMARY KEY,
        data_laikas TIMESTAMP,
        savivaldybe TEXT,
        ivykio_vieta TEXT,
        rusis TEXT,
        schema1 TEXT,
        schema2 TEXT,
        dangos_bukle TEXT,
        paros_metas TEXT,
        kelio_apsvietimas TEXT,
        meteo_salygos TEXT,
        neblaivus_kaltininkai INTEGER,
        apsvaige_kaltininkai INTEGER,
        dalyviu_skaicius INTEGER,
        zuvusiu_skaicius INTEGER,
        zuv_vaiku INTEGER,
        suzeistu_skaicius INTEGER,
        suzeista_vaiku INTEGER,
        ilguma DOUBLE PRECISION,
        platuma DOUBLE PRECISION,
        leistinas_greitis DOUBLE PRECISION,
        metai INTEGER,
        menuo INTEGER,
        diena INTEGER,
        valanda INTEGER
    );
    CREATE TABLE IF NOT EXISTS participants (
        id SERIAL PRIMARY KEY,
        dalyvis_id TEXT,
        registrokodas TEXT REFERENCES events(registrokodas) ON DELETE CASCADE,
        kategorija TEXT,
        lytis TEXT,
        amzius INTEGER,
        bukle TEXT,
        busena TEXT,
        girtumas_promilemis NUMERIC,
        kaltininkas BOOLEAN,
        dalyvio_busena TEXT,
        vairavimo_stazas NUMERIC,
        dalyvio_ket_pazeidimai TEXT
    );
       
"""
# prijungia prie DEFAULT duomenu bazes

conn = psycopg2.connect(  #nusakome kur jungtis
    dbname='postgres',
    user=PG_USER,
    password=PG_PASSWORD,
    host=PG_HOST,
    port=PG_PORT,
)
# nustato automatini patvirtinima

conn.autocommit = True
cursor = conn.cursor()
cursor.execute(
    "SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,)
)
#tikrina ar musu duomenu baze egzistuoja

if not cursor.fetchone(): #fetchone() grazina tik viena irasa
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
    print(f"Created database `{DB_NAME}`")

else:
    print(F"Database `{DB_NAME}` already exists")

# uzdarome duomenu bazes rysi
cursor.close()
conn.close()

def create_table():
    try:
        with psycopg2.connect(
            dbname=DB_NAME,
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(TABLE_SQL)
                conn.commit()
                print("Table created")
    except psycopg2.Error as e:
        print(f"Database error: {e}")
if __name__ == "__main__":
    create_table()
