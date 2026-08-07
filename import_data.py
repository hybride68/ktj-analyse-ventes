import os

import pandas as pd
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(env_path: str):
        if not os.path.exists(env_path):
            return
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

from sqlalchemy import create_engine, text


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
    "produits": r"C:\Users\user\Desktop\Projet Licence Pro\produit.csv",
    "clients": r"C:\Users\user\Desktop\Projet Licence Pro\clientele.csv",
    "boutiques": r"C:\Users\user\Desktop\Projet Licence Pro\boutiques.csv",
}


def import_csv_to_table(csv_path: str, table_name: str, df: pd.DataFrame) -> int:
    if table_name == "ventes":
        allowed_cols = [
            "id_transaction",
            "date_vente",
            "id_boutique",
            "id_client",
            "telephone_client",
            "code_produit",
            "prix_unitaire_facture",
            "quantite",
            "mode_paiement",
            "annee",
            "mois",
            "trimestre",
            "montant",
        ]
        df = df.loc[:, [col for col in allowed_cols if col in df.columns]]
        if "date_vente" in df.columns:
            df["date_vente"] = pd.to_datetime(df["date_vente"], dayfirst=True, errors="coerce")
            df["date_vente"] = df["date_vente"].dt.strftime("%Y-%m-%d")
        if "trimestre" in df.columns:
            df["trimestre"] = pd.to_numeric(df["trimestre"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
        if "id_transaction" in df.columns:
            with engine.connect() as conn:
                existing = set(row[0] for row in conn.execute(text("SELECT id_transaction FROM ventes")).all())
            df = df[~df["id_transaction"].isin(existing)]
    elif table_name == "segments_rfm":
        allowed_cols = ["id_client", "recence", "frequence", "montant", "segment"]
        df = df.loc[:, [col for col in allowed_cols if col in df.columns]]
    elif table_name == "previsions":
        allowed_cols = ["ds", "yhat", "yhat_lower", "yhat_upper"]
        df = df.loc[:, [col for col in allowed_cols if col in df.columns]]
        df = df.rename(columns={"ds": "date", "yhat": "ca_prevision", "yhat_lower": "ca_min", "yhat_upper": "ca_max"})
    elif table_name == "produits":
        allowed_cols = [
            "code_produit",
            "designation_produit",
            "categorie",
            "sous_categorie",
            "marque",
            "prix_achat_fcfa",
            "prix_vente_conseille_fcfa",
            "unite",
        ]
        df = df.loc[:, [col for col in allowed_cols if col in df.columns]]
        df = df.rename(
            columns={
                "designation_produit": "designation",
                "prix_achat_fcfa": "prix_achat",
                "prix_vente_conseille_fcfa": "prix_vente",
            }
        )
        if "code_produit" in df.columns:
            df["code_produit"] = df["code_produit"].astype(str).str.strip()
            df = df.drop_duplicates(subset=["code_produit"])
            df = df[df["code_produit"].notna() & (df["code_produit"] != "")]
            # exclude products that already exist in the DB
            with engine.connect() as conn:
                existing_codes = set(row[0] for row in conn.execute(text("SELECT code_produit FROM produits")).all())
            df = df[~df["code_produit"].isin(existing_codes)]
        for col in ["prix_achat", "prix_vente"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    elif table_name == "clients":
        allowed_cols = [
            "id_client",
            "nom_client",
            "prenom_client",
            "telephone_client",
            "region",
            "type_client",
            "statut",
        ]
        df = df.loc[:, [col for col in allowed_cols if col in df.columns]]
        df = df.rename(columns={"nom_client": "nom", "prenom_client": "prenom", "telephone_client": "telephone"})
        if "id_client" in df.columns:
            df["id_client"] = df["id_client"].astype(str).str.strip()
            df = df[df["id_client"].notna() & (df["id_client"] != "")]
            df = df.drop_duplicates(subset=["id_client"])
    elif table_name == "boutiques":
        allowed_cols = [
            "id_boutique",
            "nom_boutique",
            "ville",
            "region",
            "responsable_boutique",
            "nombre_employes",
        ]
        df = df.loc[:, [col for col in allowed_cols if col in df.columns]]
        df = df.rename(columns={"responsable_boutique": "responsable", "nombre_employes": "nb_employes"})
        if "nb_employes" in df.columns:
            df["nb_employes"] = pd.to_numeric(df["nb_employes"], errors="coerce")
        if "id_boutique" in df.columns:
            df["id_boutique"] = df["id_boutique"].astype(str).str.strip()
            df = df[df["id_boutique"].notna() & (df["id_boutique"] != "")]
            df = df.drop_duplicates(subset=["id_boutique"])

    df.to_sql(table_name, engine, if_exists="append", index=False)
    return len(df)


if __name__ == "__main__":
    ventes_df = pd.read_csv(CSV_FILES["ventes"], sep=";", encoding="utf-8")
    rfm_df = pd.read_csv(CSV_FILES["rfm"], sep=";", encoding="utf-8")
    previsions_df = pd.read_csv(CSV_FILES["previsions"], sep=";", encoding="utf-8")
    # produit.csv uses commas as separators
    produits_df = pd.read_csv(CSV_FILES["produits"], sep=",", encoding="utf-8")
    clients_df = pd.read_csv(CSV_FILES["clients"], sep=";", encoding="utf-8")
    boutiques_df = pd.read_csv(CSV_FILES["boutiques"], sep=";", encoding="utf-8")

    if "date" in previsions_df.columns:
        previsions_df["date"] = pd.to_datetime(previsions_df["date"], dayfirst=True).dt.strftime("%Y-%m-%d")

    ventes_count = import_csv_to_table(CSV_FILES["ventes"], "ventes", ventes_df)
    rfm_count = import_csv_to_table(CSV_FILES["rfm"], "segments_rfm", rfm_df)
    previsions_count = import_csv_to_table(CSV_FILES["previsions"], "previsions", previsions_df)
    produits_count = import_csv_to_table(CSV_FILES["produits"], "produits", produits_df)
    clients_count = import_csv_to_table(CSV_FILES["clients"], "clients", clients_df)
    boutiques_count = import_csv_to_table(CSV_FILES["boutiques"], "boutiques", boutiques_df)

    print(f"Ventes insérées : {ventes_count}")
    print(f"Segments RFM insérées : {rfm_count}")
    print(f"Prévisions insérées : {previsions_count}")
    print(f"Produits insérés : {produits_count}")
    print(f"Clients insérés : {clients_count}")
    print(f"Boutiques insérées : {boutiques_count}")
