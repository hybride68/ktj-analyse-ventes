from datetime import date
from pathlib import Path
import pickle
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from backend.database import get_db
    from backend.models import Prevision
    from backend.routers.auth import get_current_user
except ImportError:
    from database import get_db
    from models import Prevision
    from routers.auth import get_current_user

router = APIRouter()


def _find_project_root(start: Optional[Path] = None) -> Path:
    base = (start or Path(__file__).resolve()).resolve()
    for candidate in [base, *base.parents]:
        if (candidate / "prophet_model.pkl").exists() or (candidate / "previsions.csv").exists():
            return candidate
    return base.parents[3] if len(base.parents) >= 3 else base


def _load_forecast_frame() -> pd.DataFrame:
    project_root = _find_project_root()
    model_path = project_root / "prophet_model.pkl"
    csv_path = project_root / "previsions.csv"

    model = None
    if model_path.exists():
        with model_path.open("rb") as handle:
            model = pickle.load(handle)

    forecast_frame = None
    if csv_path.exists():
        forecast_frame = pd.read_csv(csv_path, sep=";", encoding="utf-8")
        if "ds" in forecast_frame.columns:
            forecast_frame["ds"] = pd.to_datetime(forecast_frame["ds"], errors="coerce")
            forecast_frame = forecast_frame.dropna(subset=["ds"]).copy()
            if "yhat" in forecast_frame.columns:
                forecast_frame = forecast_frame.rename(
                    columns={"yhat": "ca_prevision", "yhat_lower": "ca_min", "yhat_upper": "ca_max"}
                )
        else:
            forecast_frame = None

    if forecast_frame is None and model is not None:
        future = model.make_future_dataframe(periods=12, freq="W")
        predicted = model.predict(future)
        forecast_frame = predicted[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        forecast_frame = forecast_frame.rename(
            columns={"yhat": "ca_prevision", "yhat_lower": "ca_min", "yhat_upper": "ca_max"}
        )
        forecast_frame["ds"] = pd.to_datetime(forecast_frame["ds"], errors="coerce")
        forecast_frame = forecast_frame.dropna(subset=["ds"]).copy()

    if forecast_frame is None or forecast_frame.empty:
        return pd.DataFrame(columns=["ds", "ca_prevision", "ca_min", "ca_max"])

    if model is not None and hasattr(model, "history") and hasattr(model.history, "__len__"):
        try:
            history_ds = pd.to_datetime(model.history["ds"], errors="coerce")
            if history_ds.notna().any():
                history_end = history_ds.max()
                forecast_frame = forecast_frame[forecast_frame["ds"] > history_end].copy()
        except Exception:
            pass

    if "ca_prevision" not in forecast_frame.columns:
        forecast_frame["ca_prevision"] = 0.0
    if "ca_min" not in forecast_frame.columns:
        forecast_frame["ca_min"] = 0.0
    if "ca_max" not in forecast_frame.columns:
        forecast_frame["ca_max"] = 0.0

    forecast_frame = forecast_frame[["ds", "ca_prevision", "ca_min", "ca_max"]].copy()
    forecast_frame = forecast_frame.sort_values("ds")
    return forecast_frame.reset_index(drop=True)


@router.get("/monthly")
def get_monthly_previsions(
    year: Optional[int] = None,
    boutique: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list:
    forecast_frame = _load_forecast_frame()
    if not forecast_frame.empty:
        monthly_frame = forecast_frame.copy()
        monthly_frame["mois"] = monthly_frame["ds"].dt.to_period("M").astype(str)
        if year:
            monthly_frame = monthly_frame[monthly_frame["mois"].str.startswith(f"{year}-")]
        monthly_frame = monthly_frame.groupby("mois", as_index=False).agg(
            ca_prevision_moyenne=("ca_prevision", "sum"),
            ca_min_moyenne=("ca_min", "sum"),
            ca_max_moyenne=("ca_max", "sum"),
        )
        monthly_frame = monthly_frame.sort_values("mois")
        return [
            {
                "mois": row["mois"],
                "ca_prevision_moyenne": round(float(row["ca_prevision_moyenne"]), 2) if pd.notna(row["ca_prevision_moyenne"]) else 0,
                "ca_min_moyenne": round(float(row["ca_min_moyenne"]), 2) if pd.notna(row["ca_min_moyenne"]) else 0,
                "ca_max_moyenne": round(float(row["ca_max_moyenne"]), 2) if pd.notna(row["ca_max_moyenne"]) else 0,
            }
            for _, row in monthly_frame.iterrows()
        ]

    query = db.query(
        func.to_char(Prevision.date, "YYYY-MM").label("mois"),
        func.sum(Prevision.ca_prevision).label("ca_prevision_moyenne"),
        func.sum(Prevision.ca_min).label("ca_min_moyenne"),
        func.sum(Prevision.ca_max).label("ca_max_moyenne"),
    )
    if boutique:
        query = query.filter(Prevision.boutique_id == boutique)
    if year:
        query = query.filter(func.extract("year", Prevision.date) == year)
    previsions = (
        query
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
    year: Optional[int] = None,
    boutique: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list:
    forecast_frame = _load_forecast_frame()
    if not forecast_frame.empty:
        frame = forecast_frame.copy()
        if year:
            frame = frame[frame["ds"].dt.year == year]
        return [
            {
                "date": row["ds"].strftime("%Y-%m-%d"),
                "ca_prevision": round(float(row["ca_prevision"]), 2) if pd.notna(row["ca_prevision"]) else 0,
                "ca_min": round(float(row["ca_min"]), 2) if pd.notna(row["ca_min"]) else 0,
                "ca_max": round(float(row["ca_max"]), 2) if pd.notna(row["ca_max"]) else 0,
            }
            for _, row in frame.iterrows()
        ]

    query = db.query(
        Prevision.date,
        Prevision.ca_prevision,
        Prevision.ca_min,
        Prevision.ca_max,
    )
    if boutique:
        query = query.filter(Prevision.boutique_id == boutique)
    if year:
        query = query.filter(func.extract("year", Prevision.date) == year)
    previsions = query.order_by(Prevision.date).all()

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


@router.post("/retrain")
def retrain_previsions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    forecast_frame = _load_forecast_frame()
    if not forecast_frame.empty:
        monthly_frame = forecast_frame.copy()
        monthly_frame["mois"] = monthly_frame["ds"].dt.to_period("M")
        monthly_frame = monthly_frame.groupby("mois", as_index=False).agg(
            ca_prevision=("ca_prevision", "sum"),
            ca_min=("ca_min", "sum"),
            ca_max=("ca_max", "sum"),
        )
        monthly_frame = monthly_frame.sort_values("mois").head(3)

        created = []
        for _, row in monthly_frame.iterrows():
            forecast_date = row["mois"].to_timestamp().date()
            forecast_value = round(float(row["ca_prevision"]), 2) if pd.notna(row["ca_prevision"]) else 0
            forecast_row = Prevision(
                date=forecast_date,
                boutique_id=None,
                ca_prevision=forecast_value,
                ca_min=round(float(row["ca_min"]), 2) if pd.notna(row["ca_min"]) else 0,
                ca_max=round(float(row["ca_max"]), 2) if pd.notna(row["ca_max"]) else 0,
                modele="prophet_model.pkl",
                date_calcul=date.today(),
            )
            db.add(forecast_row)
            created.append(forecast_date.strftime("%Y-%m"))

        db.commit()
        return {"status": "ok", "created": created, "source": "prophet_model.pkl"}

    base_query = db.query(Prevision)
    base_rows = base_query.order_by(Prevision.date.desc()).limit(6).all()
    if base_rows:
        base_value = sum(item.ca_prevision or 0 for item in base_rows) / len(base_rows)
    else:
        base_value = 1000000.0

    created = []
    for month_index, month in enumerate([1, 2, 3], start=1):
        forecast_date = date(2025, month, 1)
        forecast_value = round(base_value * (1 + 0.05 * month_index), 2)
        forecast_row = Prevision(
            date=forecast_date,
            boutique_id=None,
            ca_prevision=forecast_value,
            ca_min=round(forecast_value * 0.9, 2),
            ca_max=round(forecast_value * 1.1, 2),
            modele="placeholder",
            date_calcul=date.today(),
        )
        db.add(forecast_row)
        created.append(forecast_date.strftime("%Y-%m"))

    db.commit()
    return {"status": "ok", "created": created, "source": "fallback"}
