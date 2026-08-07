import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, 'backend', '.env')
load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise SystemExit('DATABASE_URL not found')

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    print('PREVISIONS:')
    total = conn.execute(text('SELECT COUNT(*) FROM previsions')).scalar()
    distinct_dates = conn.execute(text("SELECT COUNT(DISTINCT date) FROM previsions")).scalar()
    min_date = conn.execute(text("SELECT MIN(date) FROM previsions")).scalar()
    max_date = conn.execute(text("SELECT MAX(date) FROM previsions")).scalar()
    print(' total_count:', total)
    print(' distinct_dates:', distinct_dates)
    print(' min_date:', min_date, ' max_date:', max_date)
    print('\n sample first 5 rows:')
    for row in conn.execute(text('SELECT date, ca_prevision, ca_min, ca_max FROM previsions ORDER BY date LIMIT 5')).fetchall():
        print(' ', row)
    print('\n sample last 5 rows:')
    for row in conn.execute(text('SELECT date, ca_prevision, ca_min, ca_max FROM previsions ORDER BY date DESC LIMIT 5')).fetchall():
        print(' ', row)

    print('\nSEGMENTS_RFM:')
    total_rfm = conn.execute(text('SELECT COUNT(*) FROM segments_rfm')).scalar()
    distinct_clients = conn.execute(text('SELECT COUNT(DISTINCT id_client) FROM segments_rfm')).scalar()
    segments_count = conn.execute(text("SELECT segment, COUNT(*) as c FROM segments_rfm GROUP BY segment ORDER BY c DESC LIMIT 10")).fetchall()
    print(' total_count:', total_rfm)
    print(' distinct_id_client:', distinct_clients)
    print(' top segments:', segments_count)
    print('\n sample rows:')
    for row in conn.execute(text('SELECT id_client, recence, frequence, montant, segment FROM segments_rfm LIMIT 10')).fetchall():
        print(' ', row)
