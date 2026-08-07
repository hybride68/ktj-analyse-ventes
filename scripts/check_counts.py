import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# locate project root and backend .env
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, 'backend', '.env')
load_dotenv(ENV_PATH)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise SystemExit('DATABASE_URL not found in backend/.env')

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    tables = [r[0] for r in conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))]
    tables = sorted(tables)
    print('Found tables:', ', '.join(tables))
    for t in tables:
        try:
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        except Exception as e:
            cnt = f'ERROR: {e}'
        print(f"{t}: {cnt}")
