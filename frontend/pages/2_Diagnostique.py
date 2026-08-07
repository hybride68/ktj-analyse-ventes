import os
import sys

import pandas as pd
import plotly.express as px
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

month_labels = {1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Juin", 7: "Juil", 8: "Aoû", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Déc"}

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.gemini import generate_insight

st.set_page_config(page_title="SID-Dream - Analyse Diagnostique", layout="wide")
st.title("SID-Dream — Analyse Diagnostique")

API_URL = get_api_url()
token = st.session_state.get("token")
if not token:
    st.error("Veuillez vous connecter")
    st.stop()

headers = {"Authorization": f"Bearer {token}"}

st.sidebar.header("Filtres")
selected_year = st.sidebar.selectbox("Année", ["Tout", 2022, 2023, 2024])

filters = _cached_api_json("kpis/diagnostic/filters", (), token)
if filters:
    boutique_options = ["Tout"] + filters.get("boutiques", [])
else:
    st.sidebar.warning("Impossible de charger les filtres de diagnostic. Affichage minimal activé.")
    boutique_options = ["Tout"]

selected_boutique = st.sidebar.selectbox("Boutique", boutique_options)

year_params = {} if selected_year == "Tout" else {"year": selected_year}
params = dict(year_params)
if selected_boutique != "Tout":
    params["boutique"] = selected_boutique

heatmap_df = pd.DataFrame(_cached_api_json("kpis/diagnostic/heatmap", _params_tuple(params), token))

if not heatmap_df.empty:
    heatmap_df = heatmap_df.pivot_table(index="mois", columns="annee", values="ca_total", aggfunc="sum").fillna(0)
    heatmap_df = heatmap_df.sort_index()
    month_names = [month_labels[m] for m in heatmap_df.index]
    fig_heatmap = px.imshow(
        heatmap_df.T,
        x=month_names,
        y=[str(y) for y in heatmap_df.columns],
        color_continuous_scale="viridis",
        aspect="auto",
        labels={"x": "Mois", "y": "Année", "color": "CA"},
        title="Heatmap du CA par mois et par année",
    )
    fig_heatmap.update_layout(margin=dict(t=50, b=100, l=80, r=20))
    st.plotly_chart(fig_heatmap, use_container_width=True)
    try:
        insight = generate_insight(heatmap_df.to_dict(), "Heatmap du chiffre d'affaires par mois et par année")
        st.info(insight)
    except Exception:
        st.caption("Insight IA indisponible pour le moment.")
else:
    st.info("Aucune donnée de CA mensuel disponible.")

top_df = pd.DataFrame(_cached_api_json("kpis/diagnostic/top_products", _params_tuple({**params, "limit": 10}), token))
if not top_df.empty:
    top_df = top_df.copy()
    fig_top = px.bar(
        top_df,
        x="ca_total",
        y="designation",
        orientation="h",
        text="ca_total",
        template="plotly_dark",
        title="Top 10 produits par CA",
    )
    fig_top.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_top.update_layout(margin=dict(l=240, t=50))
    st.plotly_chart(fig_top, use_container_width=True)
    try:
        insight = generate_insight(top_df.to_dict("records"), "Top 10 produits par chiffre d'affaires")
        st.info(insight)
    except Exception:
        st.caption("Insight IA indisponible pour le moment.")

subcat_df = pd.DataFrame(_cached_api_json("kpis/diagnostic/by_subcategory", _params_tuple(params), token))
if not subcat_df.empty:
    subcat_agg = subcat_df.groupby('sous_categorie', as_index=False)['ca_total'].sum()
    subcat_agg = subcat_agg.sort_values('ca_total', ascending=False)
    if subcat_agg['sous_categorie'].nunique() > 1:
        fig_sub = px.bar(
            subcat_agg,
            x="sous_categorie",
            y="ca_total",
            template="plotly_dark",
            title="CA par sous-catégorie",
        )
        fig_sub.update_layout(xaxis_tickangle=-45, margin=dict(t=50, b=100))
        st.plotly_chart(fig_sub, use_container_width=True)

weekday_df = pd.DataFrame(_cached_api_json("kpis/diagnostic/by_weekday", _params_tuple(params), token))
if not weekday_df.empty:
    fig_weekday = px.line(
        weekday_df,
        x="jour_semaine",
        y="ca_total",
        markers=True,
        template="plotly_dark",
        title="CA par jour de la semaine",
    )
    st.plotly_chart(fig_weekday, use_container_width=True)
