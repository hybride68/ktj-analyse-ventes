import os
import sys

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from frontend.api_config import get_api_url
except ImportError:
    from api_config import get_api_url

session = requests.Session()

@st.cache_data(ttl=600, show_spinner=False)
def _cached_api_json(path: str, params_tuple: tuple, token: str):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = session.get(f"{API_URL}/{path}", headers=headers, params=dict(params_tuple), timeout=10)
    return response.json() if response.status_code == 200 else []


def _params_tuple(params: dict) -> tuple:
    return tuple(sorted(params.items())) if params else ()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.gemini import generate_insight

st.set_page_config(page_title="SID-Dream - Analyse Prédictive", layout="wide")
st.title("SID-Dream — Analyse Prédictive")

API_URL = get_api_url()
token = st.session_state.get("token")
if not token:
    st.error("Veuillez vous connecter")
    st.stop()

headers = {"Authorization": f"Bearer {token}"}

params = {"year": 2025}

# phrase descriptive supprimée à la demande de l'utilisateur

params_tuple = _params_tuple(params)
monthly_df = pd.DataFrame(_cached_api_json("previsions/monthly", params_tuple, token))
weekly_df = pd.DataFrame(_cached_api_json("previsions/daily", params_tuple, token))
actual_2024_df = pd.DataFrame(_cached_api_json("kpis/monthly", _params_tuple({"year": 2024}), token))
if not actual_2024_df.empty:
    actual_2024_df["mois"] = actual_2024_df["mois"].astype(int)
    actual_2024_df = actual_2024_df.sort_values("mois")

monthly_from_weekly = pd.DataFrame()
if monthly_df.empty and weekly_df.empty:
    st.info("Aucune prévision disponible pour le moment. Vérifiez que les données 2025 ont bien été importées.")
    st.stop()

# Préparer l'agrégation mensuelle depuis les données hebdomadaires si présentes
if not weekly_df.empty:
    weekly_df["date"] = pd.to_datetime(weekly_df["date"], errors="coerce")
    weekly_df = weekly_df.dropna(subset=["date"])
    weekly_df = weekly_df[weekly_df["date"].dt.year == 2025].sort_values("date")
    weekly_df["mois"] = weekly_df["date"].dt.to_period("M").astype(str)
    try:
        monthly_from_weekly = (
            weekly_df.groupby("mois", as_index=False)
            .agg(
                ca_prevision_moyenne=("ca_prevision", "sum"),
                ca_min_moyenne=("ca_min", "sum"),
                ca_max_moyenne=("ca_max", "sum"),
            )
            .sort_values("mois")
        )
    except Exception:
        monthly_from_weekly = pd.DataFrame()
    weekly_display = weekly_df.copy()
else:
    weekly_display = pd.DataFrame({
        "date": ["2025-01-05", "2025-01-12", "2025-01-19"],
        "ca_prevision": [0, 0, 0],
        "ca_min": [0, 0, 0],
        "ca_max": [0, 0, 0],
    })

# Utiliser l'agrégation mensuelle issue des semaines si disponible, sinon la source mensuelle
if not monthly_from_weekly.empty:
    monthly_display = monthly_from_weekly.copy()
else:
    if not monthly_df.empty:
        monthly_df["mois"] = monthly_df["mois"].astype(str)
        monthly_df = monthly_df[monthly_df["mois"].str.startswith("2025")].sort_values("mois")
        monthly_display = monthly_df.copy()
    else:
        monthly_display = pd.DataFrame({
            "mois": ["2025-01", "2025-02", "2025-03"],
            "ca_prevision_moyenne": [0, 0, 0],
            "ca_min_moyenne": [0, 0, 0],
            "ca_max_moyenne": [0, 0, 0],
        })

if not monthly_display.empty:
    metric_labels = ["Jan 2025", "Fév 2025", "Mar 2025"]
    metric_keys = ["2025-01", "2025-02", "2025-03"]
    cols = st.columns(3)
    for col, label, key in zip(cols, metric_labels, metric_keys):
        value = monthly_display.loc[monthly_display["mois"] == key, "ca_prevision_moyenne"].sum()
        col.metric(label, f"{value:,.0f} FCFA")

fig = go.Figure()
if not actual_2024_df.empty:
    fig.add_trace(go.Bar(
        x=actual_2024_df["mois"].astype(str).tolist(),
        y=actual_2024_df["ca_total"].tolist(),
        name="CA réel 2024",
        marker_color='rgba(55,83,109,0.8)',
    ))
if not monthly_display.empty:
    fig.add_trace(go.Scatter(
        x=monthly_display["mois"].tolist(),
        y=monthly_display["ca_prevision_moyenne"].tolist(),
        mode="lines+markers",
        name="Prévision 2025",
        line=dict(color="rgba(255, 145, 77, 1)", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=monthly_display["mois"].tolist(),
        y=monthly_display["ca_max_moyenne"].tolist(),
        mode="lines",
        line=dict(color='rgba(255, 145, 77, 0)'),
        showlegend=False,
        hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=monthly_display["mois"].tolist(),
        y=monthly_display["ca_min_moyenne"].tolist(),
        mode="lines",
        fill='tonexty',
        fillcolor='rgba(255, 145, 77, 0.2)',
        line=dict(color='rgba(255, 145, 77, 0)'),
        name="Intervalle de confiance",
    ))
fig.update_layout(title="CA réel 2024 et prévision 2025", template="plotly_dark", yaxis=dict(tickformat=","), margin=dict(t=60))
st.plotly_chart(fig, use_container_width=True)

st.subheader("Tableau mensuel")
st.dataframe(monthly_display.rename(columns={
    "mois": "Mois",
    "ca_prevision_moyenne": "CA prévu",
    "ca_min_moyenne": "CA min",
    "ca_max_moyenne": "CA max",
}), use_container_width=True)

st.subheader("Tableau hebdomadaire")
st.dataframe(weekly_display.rename(columns={
    "date": "Date",
    "ca_prevision": "CA prévu",
    "ca_min": "CA min",
    "ca_max": "CA max",
}), use_container_width=True)

try:
    insight = generate_insight(
        {
            "mois": monthly_display["mois"].tolist(),
            "ca_prevision": monthly_display["ca_prevision_moyenne"].astype(float).tolist(),
        },
        "Prévisions mensuelles pour l'année 2025",
    )
    st.info(insight)
except Exception:
    st.caption("Insight IA indisponible pour le moment.")
