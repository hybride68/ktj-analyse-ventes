from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Client, Produit, Vente
from backend.routers.auth import get_current_user

router = APIRouter()


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    total_sales = db.query(func.coalesce(func.sum(Vente.montant), 0)).scalar() or 0
    transaction_count = db.query(Vente).count()

    ca_total = float(total_sales)
    nb_transactions = transaction_count
    panier_moyen = round(ca_total / nb_transactions, 2) if nb_transactions else 0

    nb_clients_uniques = (
        db.query(func.count(func.distinct(Vente.id_client)))
        .filter(Vente.id_client.isnot(None))
        .scalar()
        or 0
    )
    nb_produits_uniques = (
        db.query(func.count(func.distinct(Vente.code_produit)))
        .filter(Vente.code_produit.isnot(None))
        .scalar()
        or 0
    )

    return {
        "ca_total": ca_total,
        "nb_transactions": nb_transactions,
        "panier_moyen": panier_moyen,
        "nb_clients_uniques": nb_clients_uniques,
        "nb_produits_uniques": nb_produits_uniques,
    }


@router.get("/monthly")
def get_monthly_sales(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[dict]:
    rows = (
        db.query(Vente.annee, Vente.mois, func.coalesce(func.sum(Vente.montant), 0).label("ca_total"))
        .group_by(Vente.annee, Vente.mois)
        .order_by(Vente.annee, Vente.mois)
        .all()
    )

    return [
        {"annee": row.annee, "mois": row.mois, "ca_total": float(row.ca_total)}
        for row in rows
    ]


@router.get("/by_boutique")
def get_sales_by_boutique(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[dict]:
    rows = (
        db.query(
            Vente.id_boutique,
            func.coalesce(func.sum(Vente.montant), 0).label("ca_total"),
        )
        .group_by(Vente.id_boutique)
        .order_by(func.coalesce(func.sum(Vente.montant), 0).desc())
        .all()
    )

    return [
        {"id_boutique": row.id_boutique, "ca_total": float(row.ca_total)}
        for row in rows
    ]


@router.get("/by_paiement")
def get_sales_by_paiement(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[dict]:
    rows = (
        db.query(
            Vente.mode_paiement,
            func.coalesce(func.sum(Vente.montant), 0).label("ca_total"),
        )
        .group_by(Vente.mode_paiement)
        .all()
    )

    return [
        {"mode_paiement": row.mode_paiement, "ca_total": float(row.ca_total)}
        for row in rows
    ]
