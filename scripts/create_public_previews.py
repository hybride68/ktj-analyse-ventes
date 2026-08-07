import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT,'backend','.env'))
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    conn.execute(text('DROP TABLE IF EXISTS public.previsions_preview'))
    conn.execute(text("CREATE TABLE public.previsions_preview AS SELECT DISTINCT ON (date) * FROM public.previsions ORDER BY date, id"))
    conn.execute(text('DROP TABLE IF EXISTS public.segments_rfm_preview'))
    conn.execute(text("CREATE TABLE public.segments_rfm_preview AS SELECT DISTINCT ON (id_client) * FROM public.segments_rfm ORDER BY id_client, id"))

with engine.connect() as conn:
    pv_preview = conn.execute(text('SELECT COUNT(*) FROM public.previsions_preview')).scalar()
    rfm_preview = conn.execute(text('SELECT COUNT(*) FROM public.segments_rfm_preview')).scalar()
    print('Created public.previsions_preview:', pv_preview)
    print('Created public.segments_rfm_preview:', rfm_preview)
