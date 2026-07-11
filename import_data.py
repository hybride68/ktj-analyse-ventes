import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "backend", ".env")
load_dotenv(ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL introuvable. Vérifiez backend/.env")

engine = create_engine(DATABASE_URL)

CSV_FILES = {
    "ventes": r"C:\Users\user\Desktop\Projet Licence Pro\ventes_final.csv",
    "rfm": r"C:\Users\user\Desktop\Projet Licence Pro\rfm_segments.csv",
    "previsions": r"C:\Users\user\Desktop\Projet Licence Pro\previsions.csv",
}


def import_csv_to_table(csv_path: str, table_name: str, df: pd.DataFrame) -> int:
    df.to_sql(table_name, engine, if_exists="append", index=False)
    return len(df)


if __name__ == "__main__":
    ventes_df = pd.read_csv(CSV_FILES["ventes"], sep=";", encoding="utf-8")
    rfm_df = pd.read_csv(CSV_FILES["rfm"], sep=";", encoding="utf-8")
    previsions_df = pd.read_csv(CSV_FILES["previsions"], sep=";", encoding="utf-8")

    if "date" in previsions_df.columns:
        previsions_df["date"] = pd.to_datetime(previsions_df["date"], dayfirst=True).dt.strftime("%Y-%m-%d")

    ventes_count = import_csv_to_table(CSV_FILES["ventes"], "ventes", ventes_df)
    rfm_count = import_csv_to_table(CSV_FILES["rfm"], "segments_rfm", rfm_df)
    previsions_count = import_csv_to_table(CSV_FILES["previsions"], "previsions", previsions_df)

    print(f"Ventes insérées : {ventes_count}")
    print(f"Segments RFM insérés : {rfm_count}")
    print(f"Prévisions insérées : {previsions_count}")
