from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from backend.models import Boutique, Client, Produit, Vente


DATASETS: dict[str, dict[str, Any]] = {
    "ventes": {
        "model": Vente,
        "required": [
            "id_transaction",
            "date_vente",
            "id_boutique",
            "code_produit",
            "prix_unitaire_facture",
            "quantite",
            "montant",
        ],
        "aliases": {},
    },
    "produits": {
        "model": Produit,
        "required": ["code_produit", "designation", "categorie"],
        "aliases": {
            "designation_produit": "designation",
            "prix_achat_fcfa": "prix_achat",
            "prix_vente_conseille_fcfa": "prix_vente",
        },
    },
    "clients": {
        "model": Client,
        "required": ["id_client", "nom"],
        "aliases": {
            "nom_client": "nom",
            "prenom_client": "prenom",
            "telephone_client": "telephone",
        },
    },
    "boutiques": {
        "model": Boutique,
        "required": ["id_boutique", "nom_boutique"],
        "aliases": {
            "responsable_boutique": "responsable",
            "nombre_employes": "nb_employes",
        },
    },
}


def _read_csv(content: bytes) -> pd.DataFrame:
    return pd.read_csv(BytesIO(content), sep=None, engine="python", encoding="utf-8-sig")


def _normalise_columns(frame: pd.DataFrame, aliases: dict[str, str]) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    frame = frame.rename(columns=aliases)
    return frame


def _clean_frame(dataset: str, frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    config = DATASETS[dataset]
    frame = _normalise_columns(frame, config["aliases"])
    errors: list[dict[str, Any]] = []
    missing = [column for column in config["required"] if column not in frame.columns]
    if missing:
        return pd.DataFrame(), [{"ligne": None, "champ": column, "message": "Colonne obligatoire absente"} for column in missing]

    allowed = set(config["model"].__table__.columns.keys())
    frame = frame[[column for column in frame.columns if column in allowed]].copy()

    for column in config["required"]:
        empty = frame[column].isna() | frame[column].astype(str).str.strip().eq("")
        for index in frame.index[empty]:
            errors.append({"ligne": int(index) + 2, "champ": column, "message": "Valeur obligatoire absente"})

    if dataset == "ventes":
        frame["date_vente"] = pd.to_datetime(frame["date_vente"], dayfirst=True, errors="coerce")
        for column in ["prix_unitaire_facture", "quantite", "montant"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if "annee" not in frame:
            frame["annee"] = frame["date_vente"].dt.year
        if "mois" not in frame:
            frame["mois"] = frame["date_vente"].dt.month
        if "trimestre" not in frame:
            frame["trimestre"] = frame["date_vente"].dt.quarter
        checks = {
            "date_vente": frame["date_vente"].isna(),
            "prix_unitaire_facture": frame["prix_unitaire_facture"] < 0,
            "quantite": frame["quantite"] <= 0,
            "montant": frame["montant"] < 0,
        }
        messages = {
            "date_vente": "Date invalide",
            "prix_unitaire_facture": "Le prix doit être positif ou nul",
            "quantite": "La quantité doit être supérieure à zéro",
            "montant": "Le montant doit être positif ou nul",
        }
        for column, invalid in checks.items():
            for index in frame.index[invalid.fillna(True)]:
                errors.append({"ligne": int(index) + 2, "champ": column, "message": messages[column]})
    elif dataset in {"produits", "boutiques"}:
        numeric_columns = ["prix_achat", "prix_vente"] if dataset == "produits" else ["nb_employes"]
        for column in numeric_columns:
            if column in frame:
                frame[column] = pd.to_numeric(frame[column], errors="coerce")

    key = config["model"].__table__.primary_key.columns.values()[0].name
    duplicate_rows = frame[frame[key].duplicated(keep="first")]
    for index in duplicate_rows.index:
        errors.append({"ligne": int(index) + 2, "champ": key, "message": "Doublon dans le fichier"})

    invalid_indexes = {item["ligne"] - 2 for item in errors if item["ligne"] is not None}
    valid = frame.drop(index=[index for index in invalid_indexes if index in frame.index]).copy()
    valid = valid.where(pd.notna(valid), None)
    if dataset == "ventes":
        valid["date_vente"] = valid["date_vente"].apply(lambda value: value.date() if hasattr(value, "date") else value)
    return valid, errors


def validate_and_import(db: Session, dataset: str, content: bytes) -> dict[str, Any]:
    if dataset not in DATASETS:
        raise ValueError("Type de données non supporté")
    try:
        frame = _read_csv(content)
    except Exception as exc:
        raise ValueError(f"Fichier CSV illisible : {exc}") from exc
    if frame.empty:
        raise ValueError("Le fichier ne contient aucune ligne")

    valid, errors = _clean_frame(dataset, frame)
    config = DATASETS[dataset]
    table_name = config["model"].__tablename__
    key = config["model"].__table__.primary_key.columns.values()[0].name
    existing = {row[0] for row in db.execute(text(f"SELECT {key} FROM {table_name}"))}
    existing_mask = valid[key].isin(existing)
    for index in valid.index[existing_mask]:
        errors.append({"ligne": int(index) + 2, "champ": key, "message": "Enregistrement déjà présent en base"})
    valid = valid.loc[~existing_mask].copy()

    inserted = 0
    if not valid.empty:
        columns = [column.name for column in inspect(config["model"]).columns]
        valid = valid[[column for column in columns if column in valid.columns]]
        valid.to_sql(table_name, db.bind, if_exists="append", index=False)
        inserted = len(valid)
    db.commit()
    return {
        "dataset": dataset,
        "lignes_lues": len(frame),
        "lignes_inserees": inserted,
        "lignes_rejetees": len(frame) - inserted,
        "erreurs": errors[:100],
        "total_erreurs": len(errors),
    }
