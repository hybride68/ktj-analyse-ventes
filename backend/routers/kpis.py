from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from backend.database import get_db
    from backend.models import Produit, Vente
    from backend.routers.auth import get_current_user
except ImportError:
    from database import get_db
    from models import Produit, Vente
    from routers.auth import get_current_user


def _apply_user_scope(query, current_user):
    return query

router = APIRouter()


@router.get("/summary")
def get_summary(
    year: Optional[int] = None,
    boutique: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    query = _apply_user_scope(db.query(func.coalesce(func.sum(Vente.montant), 0)), current_user)
    if boutique:
        query = query.filter(Vente.id_boutique == boutique)
    total_sales_q = query
    if year:
        total_sales_q = total_sales_q.filter(Vente.annee == year)
    total_sales = total_sales_q.scalar() or 0

    transaction_q = _apply_user_scope(db.query(Vente), current_user)
    if boutique:
        transaction_q = transaction_q.filter(Vente.id_boutique == boutique)
    if year:
        transaction_q = transaction_q.filter(Vente.annee == year)
    transaction_count = transaction_q.count()

    ca_total = float(total_sales)
    nb_transactions = transaction_count
    panier_moyen = round(ca_total / nb_transactions, 2) if nb_transactions else 0

    clients_q = (
        _apply_user_scope(db.query(func.count(func.distinct(Vente.id_client))), current_user)
        .filter(Vente.id_client.isnot(None))
    )
    if boutique:
        clients_q = clients_q.filter(Vente.id_boutique == boutique)
    if year:
        clients_q = clients_q.filter(Vente.annee == year)
    nb_clients_uniques = clients_q.scalar() or 0

    produits_q = (
        _apply_user_scope(db.query(func.count(func.distinct(Vente.code_produit))), current_user)
        .filter(Vente.code_produit.isnot(None))
    )
    if boutique:
        produits_q = produits_q.filter(Vente.id_boutique == boutique)
    if year:
        produits_q = produits_q.filter(Vente.annee == year)
    nb_produits_uniques = produits_q.scalar() or 0

    return {
        "ca_total": ca_total,
        "nb_transactions": nb_transactions,
        "panier_moyen": panier_moyen,
        "nb_clients_uniques": nb_clients_uniques,
        "nb_produits_uniques": nb_produits_uniques,
    }


@router.get("/monthly")
def get_monthly_sales(
    year: Optional[int] = None,
    boutique: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[dict]:
    query = (
        _apply_user_scope(
            db.query(Vente.annee, Vente.mois, func.coalesce(func.sum(Vente.montant), 0).label("ca_total")),
            current_user,
        )
        .group_by(Vente.annee, Vente.mois)
        .order_by(Vente.annee, Vente.mois)
    )
    if boutique:
        query = query.filter(Vente.id_boutique == boutique)
    if year:
        query = query.filter(Vente.annee == year)
    rows = query.all()

    return [
        {"annee": row.annee, "mois": row.mois, "ca_total": float(row.ca_total)}
        for row in rows
    ]


@router.get("/by_boutique")
def get_sales_by_boutique(
    year: Optional[int] = None,
    boutique: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[dict]:
    query = (
        _apply_user_scope(
            db.query(
                Vente.id_boutique,
                func.coalesce(func.sum(Vente.montant), 0).label("ca_total"),
            ),
            current_user,
        )
        .group_by(Vente.id_boutique)
        .order_by(func.coalesce(func.sum(Vente.montant), 0).desc())
    )
    if boutique:
        query = query.filter(Vente.id_boutique == boutique)
    if year:
        query = query.filter(Vente.annee == year)
    rows = query.all()

    return [
        {"id_boutique": row.id_boutique, "ca_total": float(row.ca_total)}
        for row in rows
    ]


@router.get("/by_paiement")
def get_sales_by_paiement(
    year: Optional[int] = None,
    boutique: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[dict]:
    query = (
        _apply_user_scope(
            db.query(
                Vente.mode_paiement,
                func.coalesce(func.sum(Vente.montant), 0).label("ca_total"),
            ),
            current_user,
        )
        .group_by(Vente.mode_paiement)
    )
    if boutique:
        query = query.filter(Vente.id_boutique == boutique)
    if year:
        query = query.filter(Vente.annee == year)
    rows = query.all()

    return [
        {"mode_paiement": row.mode_paiement, "ca_total": float(row.ca_total)}
        for row in rows
    ]


@router.get("/diagnostic/heatmap")
def get_diagnostic_heatmap(
    year: Optional[int] = None,
    category: Optional[str] = None,
    boutique: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[dict]:
    query = _apply_user_scope(
        db.query(Vente.annee, Vente.mois, func.coalesce(func.sum(Vente.montant), 0).label("ca_total")),
        current_user,
    )
    if year:
        query = query.filter(Vente.annee == year)
    if boutique:
        query = query.filter(Vente.id_boutique == boutique)
    if category:
        query = query.join(Produit, func.trim(Produit.code_produit) == func.trim(Vente.code_produit))
        query = query.filter(Produit.categorie == category)

    rows = query.group_by(Vente.annee, Vente.mois).order_by(Vente.annee, Vente.mois).all()
    return [
        {"annee": row.annee, "mois": row.mois, "ca_total": float(row.ca_total)}
        for row in rows
    ]


@router.get("/diagnostic/top_products")
def get_diagnostic_top_products(
    year: Optional[int] = None,
    category: Optional[str] = None,
    boutique: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[dict]:
    query = (
        _apply_user_scope(
            db.query(
                Vente.code_produit,
                Produit.designation,
                func.coalesce(func.sum(Vente.montant), 0).label("ca_total"),
            ),
            current_user,
        )
        .join(Produit, func.trim(Produit.code_produit) == func.trim(Vente.code_produit))
        .group_by(Vente.code_produit, Produit.designation)
        .order_by(func.coalesce(func.sum(Vente.montant), 0).desc())
    )
    if year:
        query = query.filter(Vente.annee == year)
    if boutique:
        query = query.filter(Vente.id_boutique == boutique)
    if category:
        query = query.filter(Produit.categorie == category)

    rows = query.limit(limit).all()
    return [
        {
            "code_produit": row.code_produit,
            "designation": row.designation or row.code_produit,
            "ca_total": float(row.ca_total),
        }
        for row in rows
    ]


@router.get("/diagnostic/by_subcategory")
def get_diagnostic_by_subcategory(
    year: Optional[int] = None,
    category: Optional[str] = None,
    boutique: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[dict]:
    query = (
        _apply_user_scope(
            db.query(
                Produit.sous_categorie,
                func.coalesce(func.sum(Vente.montant), 0).label("ca_total"),
            ),
            current_user,
        )
        .join(Produit, func.trim(Produit.code_produit) == func.trim(Vente.code_produit))
        .group_by(Produit.sous_categorie)
        .order_by(func.coalesce(func.sum(Vente.montant), 0).desc())
    )
    if year:
        query = query.filter(Vente.annee == year)
    if boutique:
        query = query.filter(Vente.id_boutique == boutique)
    if category:
        query = query.filter(Produit.categorie == category)

    rows = query.all()
    return [
        {"sous_categorie": row.sous_categorie or "Non renseignée", "ca_total": float(row.ca_total)}
        for row in rows
    ]


@router.get("/diagnostic/by_weekday")
def get_diagnostic_by_weekday(
    year: Optional[int] = None,
    category: Optional[str] = None,
    boutique: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[dict]:
    weekday_expr = func.extract("dow", Vente.date_vente)
    query = _apply_user_scope(
        db.query(weekday_expr.label("weekday"), func.coalesce(func.sum(Vente.montant), 0).label("ca_total")),
        current_user,
    )
    if year:
        query = query.filter(Vente.annee == year)
    if boutique:
        query = query.filter(Vente.id_boutique == boutique)
    if category:
        query = query.join(Produit, func.trim(Produit.code_produit) == func.trim(Vente.code_produit))
        query = query.filter(Produit.categorie == category)

    rows = query.group_by(weekday_expr).order_by(weekday_expr).all()
    weekdays = {
        0: "Dimanche",
        1: "Lundi",
        2: "Mardi",
        3: "Mercredi",
        4: "Jeudi",
        5: "Vendredi",
        6: "Samedi",
    }
    return [
        {"jour_semaine": weekdays.get(int(row.weekday), str(row.weekday)), "ca_total": float(row.ca_total)}
        for row in rows
    ]


@router.get("/diagnostic/filters")
def get_diagnostic_filters(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    categories = [row[0] for row in db.query(Produit.categorie).distinct().order_by(Produit.categorie).all() if row[0]]
    boutiques = [row[0] for row in db.query(Vente.id_boutique).distinct().order_by(Vente.id_boutique).all() if row[0]]
    return {"categories": categories, "boutiques": boutiques}
