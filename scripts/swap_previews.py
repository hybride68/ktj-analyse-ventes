import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, 'backend', '.env')
load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise SystemExit('DATABASE_URL not found')

engine = create_engine(DATABASE_URL)

ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
previews = [
    ('previsions_preview', 'previsions'),
    ('segments_rfm_preview', 'segments_rfm'),
]

with engine.connect() as conn:
    trans = conn.begin()
    try:
        for preview, target in previews:
            # ensure preview exists
            exists = conn.execute(text("SELECT to_regclass(:t)"), {"t": preview}).scalar()
            if not exists:
                raise RuntimeError(f'Preview table {preview} does not exist')
            # backup original if exists
            orig_exists = conn.execute(text("SELECT to_regclass(:t)"), {"t": target}).scalar()
            if orig_exists:
                backup_name = f"{target}_backup_{ts}"
                conn.execute(text(f"ALTER TABLE {target} RENAME TO {backup_name}"))
                print(f"Renamed {target} -> {backup_name}")
            # rename preview to target
            conn.execute(text(f"ALTER TABLE {preview} RENAME TO {target}"))
            print(f"Renamed {preview} -> {target}")
        # fix sequences for serial PKs if any
        conn.execute(text("SELECT pg_catalog.setval(pg_get_serial_sequence('previsions','id'), COALESCE((SELECT MAX(id) FROM previsions),0))"))
        conn.execute(text("SELECT pg_catalog.setval(pg_get_serial_sequence('segments_rfm','id'), COALESCE((SELECT MAX(id) FROM segments_rfm),0))"))
        trans.commit()
    except Exception as e:
        trans.rollback()
        raise

with engine.connect() as conn:
    for t in ['previsions','segments_rfm']:
        cnt = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"{t}: {cnt}")

print('\nSwap complete. Originals backed up with suffix _backup_<timestamp>')
