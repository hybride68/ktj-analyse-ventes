import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

backend_dir = os.path.dirname(__file__)
project_root = os.path.dirname(backend_dir)
for env_path in [
    os.path.join(backend_dir, ".env"),
    os.path.join(project_root, ".env"),
]:
    if os.path.exists(env_path):
        load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL est introuvable. Vérifiez le fichier .env.")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "utilisateurs" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("utilisateurs")}
    if "role" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE utilisateurs ADD COLUMN role VARCHAR"))
    if "boutique_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE utilisateurs ADD COLUMN boutique_id VARCHAR"))
    if "is_active" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE utilisateurs ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))

    if "previsions" in inspector.get_table_names():
        previsions_columns = {column["name"] for column in inspector.get_columns("previsions")}
        if "boutique_id" not in previsions_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE previsions ADD COLUMN boutique_id VARCHAR"))


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
