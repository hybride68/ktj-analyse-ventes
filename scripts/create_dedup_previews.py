import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, 'backend', '.env')
load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise SystemExit('DATABASE_URL not found')

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Create dedup preview for previsions: one row per date
    conn.execute(text('DROP TABLE IF EXISTS previsions_preview'))
    conn.execute(text('''
        CREATE TABLE previsions_preview AS
        SELECT DISTINCT ON (date) *
        FROM previsions
        ORDER BY date, id
    '''))
    # Create dedup preview for segments_rfm: one row per id_client
    conn.execute(text('DROP TABLE IF EXISTS segments_rfm_preview'))
    conn.execute(text('''
        CREATE TABLE segments_rfm_preview AS
        SELECT DISTINCT ON (id_client) *
        FROM segments_rfm
        ORDER BY id_client, id
    '''))

    # report counts and samples
    pv_total = conn.execute(text('SELECT COUNT(*) FROM previsions')).scalar()
    pv_preview = conn.execute(text('SELECT COUNT(*) FROM previsions_preview')).scalar()
    print('previsions: original_count=', pv_total, ' preview_count=', pv_preview)
    print('sample from previsions_preview:')
    for r in conn.execute(text('SELECT date, ca_prevision FROM previsions_preview ORDER BY date LIMIT 5')):
        print(' ', r)

    rfm_total = conn.execute(text('SELECT COUNT(*) FROM segments_rfm')).scalar()
    rfm_preview = conn.execute(text('SELECT COUNT(*) FROM segments_rfm_preview')).scalar()
    print('\nsegments_rfm: original_count=', rfm_total, ' preview_count=', rfm_preview)
    print('top segments in preview:')
    for r in conn.execute(text('SELECT segment, COUNT(*) FROM segments_rfm_preview GROUP BY segment ORDER BY COUNT(*) DESC LIMIT 10')):
        print(' ', r)

print('\nPreviews created: previsions_preview, segments_rfm_preview. Review before swapping.')
