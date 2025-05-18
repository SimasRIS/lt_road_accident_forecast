import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

load_dotenv()

PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = os.getenv('PG_PORT', '5432')
#NUSAKOME DUOMENU BAZES PAVADINIMA, STULPELIUS IR SUKURIAM PACIA LENTELE


DB_NAME = os.getenv('DB_NAME')
TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS events (
        registrokodas TEXT PRIMARY KEY,
        dataLaikas TIMESTAMP,
        savivaldybe TEXT,
        ivykioVieta TEXT,
        rusis TEXT,
        schema1 TEXT,
        schema2 TEXT,
        dangosBukle TEXT,
        parosMetas TEXT,
        kelioApsvietimas TEXT,
        meteoSalygos TEXT,
        neblaivusKaltininkai INTEGER,
        apsvaigeKaltininkai INTEGER,
        dalyviuSkaicius INTEGER,
        zuvusiuSkaicius INTEGER,
        zuvVaiku INTEGER,
        suzeistuSkaicius INTEGER,
        suzeistaVaiku INTEGER,
        ilguma DOUBLE PRECISION,
        platuma DOUBLE PRECISION,
        leistinasGreitis DOUBLE PRECISION,
        metai INTEGER,
        menuo INTEGER,
        diena INTEGER,
        valanda INTEGER
    );
    CREATE TABLE IF NOT EXISTS participants (
        id SERIAL PRIMARY KEY,
        dalyvisId TEXT,
        registrokodas TEXT REFERENCES events(registrokodas) ON DELETE CASCADE,
        kategorija TEXT,
        lytis TEXT,
        amzius INTEGER,
        bukle TEXT,
        busena TEXT,
        girtumasPromilemis NUMERIC,
        kaltininkas BOOLEAN,
        dalyvioBusena TEXT,
        vairavimoStazas NUMERIC,
        dalyvioKetPazeidimai TEXT
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
