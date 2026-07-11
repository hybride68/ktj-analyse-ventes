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
