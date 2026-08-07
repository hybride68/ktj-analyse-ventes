import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, 'backend', '.env'))
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    raise SystemExit('DATABASE_URL not found')

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    rows = conn.execute(text("SELECT email FROM utilisateurs ORDER BY email")).fetchall()
    print('ALL EMAILS:')
    for row in rows:
        print(' ', row[0])
    print('\nEXISTS admin@pme.com:', any(row[0].lower() == 'admin@pme.com' for row in rows))
    print('EXISTS admin@pme.cm:', any(row[0].lower() == 'admin@pme.cm' for row in rows))
