from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Prevision
from backend.routers.auth import get_current_user

router = APIRouter()


@router.get("/monthly")
def get_monthly_previsions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list:
    previsions = (
        db.query(
            func.to_char(Prevision.date, "YYYY-MM").label("mois"),
            func.avg(Prevision.ca_prevision).label("ca_prevision_moyenne"),
            func.avg(Prevision.ca_min).label("ca_min_moyenne"),
            func.avg(Prevision.ca_max).label("ca_max_moyenne"),
        )
        .group_by(func.to_char(Prevision.date, "YYYY-MM"))
        .order_by(func.to_char(Prevision.date, "YYYY-MM"))
        .all()
    )

    result = [
        {
            "mois": prev[0],
            "ca_prevision_moyenne": round(prev[1], 2) if prev[1] else 0,
            "ca_min_moyenne": round(prev[2], 2) if prev[2] else 0,
            "ca_max_moyenne": round(prev[3], 2) if prev[3] else 0,
        }
        for prev in previsions
    ]
    return result


@router.get("/daily")
def get_daily_previsions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list:
    previsions = (
        db.query(
            Prevision.date,
            Prevision.ca_prevision,
            Prevision.ca_min,
            Prevision.ca_max,
        )
        .order_by(Prevision.date)
        .all()
    )

    result = [
        {
            "date": str(prev[0]),
            "ca_prevision": float(prev[1]) if prev[1] else 0,
            "ca_min": float(prev[2]) if prev[2] else 0,
            "ca_max": float(prev[3]) if prev[3] else 0,
        }
        for prev in previsions
    ]
    return result
