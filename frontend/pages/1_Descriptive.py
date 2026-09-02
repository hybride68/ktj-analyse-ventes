import json
import os
import sys
from datetime import datetime
from io import BytesIO

import os
import sys

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import streamlit as st
import pandas as pd
import plotly.express as px
import requests

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
from frontend.theme import apply_theme, render_sidebar, render_account_card
from frontend.components.kpi_cards import render_kpi_cards
from backend.gemini import generate_insights_batch

if not st.session_state.get("app_shell_active", False):
    st.set_page_config(page_title="SID-Dream - Analyse Descriptive", layout="wide", initial_sidebar_state="expanded")
    apply_theme()
    render_sidebar("Descriptive")
else:
    apply_theme()
    render_sidebar("Descriptive")

st.title("SID-Dream — Analyse Descriptive")

# CSS responsive : réduit la hauteur des graphiques Plotly sur mobile
st.markdown(
    """
    <style>
      @media (max-width: 480px) {
        .stPlotlyChart, .stPlotlyChart iframe {
          height: 350px !important;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_batch_insights(specs_tuple: tuple) -> dict:
    """
    Cache (TTL 1h) un appel batch Gemini.
    `specs_tuple` est un tuple de chaînes JSON lisibles.
    """
    specs = [json.loads(spec) for spec in specs_tuple]
    return generate_insights_batch(specs)


def _collect_specs(*, monthly_df, boutique_df, paiement_df) -> list[dict]:
    """Construit la liste des specs d'insights à générer (1 par graphique disponible)."""
    specs = []
    if monthly_df is not None and not monthly_df.empty:
        specs.append({
            "key": "monthly",
            "data": monthly_df[["annee", "mois", "ca_total"]].to_dict(orient="records"),
            "context": "Évolution mensuelle du chiffre d'affaires",
        })
    if boutique_df is not None and not boutique_df.empty:
        specs.append({
            "key": "boutique",
            "data": boutique_df.to_dict(orient="records"),
            "context": "Répartition du chiffre d'affaires par boutique",
        })
    if paiement_df is not None and not paiement_df.empty:
        specs.append({
            "key": "paiement",
            "data": paiement_df.to_dict(orient="records"),
            "context": "Répartition du chiffre d'affaires par mode de paiement",
        })
    return specs


def _format_value(metric: str, value: float) -> str:
    if metric == "ca_total":
        return f"{value:,.0f} FCFA"
    if metric == "panier_moyen":
        return f"{value:,.0f} FCFA"
    return str(value)


def _render_executive_summary(kpis: dict, monthly_df: pd.DataFrame, boutique: str, year: str) -> None:
    """Affiche un résumé exécutif adapté aux décideurs."""
    scope_label = "toutes boutiques" if boutique == "Tout" else f"la boutique {boutique}"
    period_label = "toutes années" if year == "Tout" else f"l'année {year}"

    summary_messages = []
    summary_messages.append(
        f"**CA total ({scope_label}, {period_label}) :** {_format_value('ca_total', kpis.get('ca_total', 0))}"
    )
    summary_messages.append(
        f"**Panier moyen :** {_format_value('panier_moyen', kpis.get('panier_moyen', 0))}"
    )
    summary_messages.append(
        f"**Transactions :** {int(kpis.get('nb_transactions', 0))} ventes enregistrées"
    )

    if not monthly_df.empty:
        sorted_monthly = monthly_df.sort_values(['annee', 'mois'])
        if len(sorted_monthly) >= 2:
            last = sorted_monthly.iloc[-1]['ca_total']
            prev = sorted_monthly.iloc[-2]['ca_total']
            diff = last - prev
            diff_label = _format_value('ca_total', abs(diff))
            direction = 'en hausse' if diff >= 0 else 'en baisse'
            summary_messages.append(
                f"Tendance récente : {direction} de {diff_label} entre les deux derniers mois disponibles."
            )

    top_boutique_label = None
    if not monthly_df.empty and 'id_boutique' in monthly_df.columns:
        top_boutique = monthly_df.sort_values('ca_total', ascending=False).iloc[0]
        top_boutique_label = f"Meilleure boutique : {top_boutique['id_boutique']} avec {_format_value('ca_total', top_boutique['ca_total'])}."
    elif not kpis.get('nb_transactions'):
        top_boutique_label = "Données de boutiques insuffisantes pour calculer le meilleur point de vente."

    st.markdown("### Résumé exécutif")
    for message in summary_messages:
        st.markdown(f"- {message}")
    if top_boutique_label:
        st.markdown(f"- {top_boutique_label}")

    st.markdown(
        "#### Recommandations rapides"
        "\n- Vérifier les actions promotionnelles sur les boutiques déficitaires."
        "\n- Renforcer le suivi des stocks si le panier moyen augmente fortement."
        "\n- Prioriser la boutique la plus performante pour des tests d'offre."
    )


def _build_dashboard_pdf(
    kpis: dict,
    monthly_df: pd.DataFrame,
    boutique_df: pd.DataFrame,
    paiement_df: pd.DataFrame,
    insights: dict[str, str],
    year: str,
    boutique: str,
) -> bytes:
    """Génère une synthèse PDF autonome à partir des données déjà affichées."""
    output = BytesIO()
    with PdfPages(output) as pdf:
        figure = plt.figure(figsize=(11.69, 8.27), facecolor="#10151d")
        figure.text(0.06, 0.92, "SID-Dream - Dashboard commercial", color="white", fontsize=22, weight="bold")
        figure.text(
            0.06,
            0.875,
            f"Périmètre : {boutique} | Année : {year} | Exporté le {datetime.now():%d/%m/%Y à %H:%M}",
            color="#9aa8bb",
            fontsize=10,
        )

        kpi_items = [
            ("CA total", f"{float(kpis.get('ca_total', 0)):,.0f} FCFA"),
            ("Transactions", f"{int(kpis.get('nb_transactions', 0)):,}"),
            ("Panier moyen", f"{float(kpis.get('panier_moyen', 0)):,.0f} FCFA"),
            ("Clients uniques", f"{int(kpis.get('nb_clients_uniques', 0)):,}"),
        ]
        for index, (label, value) in enumerate(kpi_items):
            left = 0.06 + index * 0.235
            figure.text(left, 0.77, label, color="#9aa8bb", fontsize=10)
            figure.text(left, 0.72, value, color="#f4d36b", fontsize=17, weight="bold")

        axes = figure.subplots(1, 2)
        if not monthly_df.empty:
            monthly_plot = monthly_df.copy()
            monthly_plot["label"] = monthly_plot["mois"].astype(str) + "/" + monthly_plot["annee"].astype(str)
            axes[0].plot(monthly_plot["label"], monthly_plot["ca_total"], color="#31d0b1", marker="o")
            axes[0].set_title("Évolution mensuelle du CA", color="white")
            axes[0].tick_params(axis="x", rotation=45, labelsize=7)
        else:
            axes[0].text(0.5, 0.5, "Aucune donnée mensuelle", ha="center", color="white")
        if not boutique_df.empty:
            axes[1].barh(boutique_df["id_boutique"].astype(str), boutique_df["ca_total"], color="#f4d36b")
            axes[1].set_title("CA par boutique", color="white")
        else:
            axes[1].text(0.5, 0.5, "Aucune donnée boutique", ha="center", color="white")
        for axis in axes:
            axis.set_facecolor("#161d27")
            axis.tick_params(colors="#dce5f1")
            for spine in axis.spines.values():
                spine.set_color("#334154")
            axis.grid(axis="y", color="#334154", alpha=0.35)
            axis.title.set_color("white")
        figure.tight_layout(rect=(0.04, 0.2, 0.96, 0.68))
        pdf.savefig(figure, facecolor=figure.get_facecolor())
        plt.close(figure)

        detail = plt.figure(figsize=(11.69, 8.27), facecolor="#10151d")
        detail.text(0.06, 0.92, "Répartition et insights", color="white", fontsize=20, weight="bold")
        if not paiement_df.empty:
            payment_axis = detail.add_axes((0.08, 0.48, 0.38, 0.32))
            payment_axis.pie(paiement_df["ca_total"], labels=paiement_df["mode_paiement"], autopct="%.1f%%")
            payment_axis.set_title("CA par mode de paiement", color="white")
        insight_text = "\n\n".join(
            f"{title.capitalize()} : {text}" for title, text in insights.items() if text
        ) or "Aucun insight disponible."
        detail.text(0.54, 0.78, "Insights IA", color="#f4d36b", fontsize=14, weight="bold")
        detail.text(0.54, 0.72, insight_text, color="white", fontsize=10, wrap=True, va="top", linespacing=1.6)
        detail.text(0.06, 0.1, "Document généré par SID-Dream", color="#9aa8bb", fontsize=9)
        pdf.savefig(detail, facecolor=detail.get_facecolor())
        plt.close(detail)
    return output.getvalue()


API_URL = get_api_url()
token = st.session_state.get("token")
if not token:
    st.error("Veuillez vous connecter")
    st.stop()

headers = {"Authorization": f"Bearer {token}"}

try:
    st.sidebar.header("Filtres")
    selected_year = st.sidebar.selectbox("Année", ["Tout", 2022, 2023, 2024])
    boutiques = _cached_api_json("auth/boutiques", (), token)
    boutique_options = ["Tout"] + [item["id_boutique"] for item in boutiques] if boutiques else ["Tout"]
    selected_boutique = st.sidebar.selectbox("Boutique", boutique_options)
    render_account_card()
    year_params = {} if selected_year == "Tout" else {"year": selected_year}
    if selected_boutique != "Tout":
        year_params["boutique"] = selected_boutique

    # --- Récupération des données (4 appels API backend) ---
    params_tuple = _params_tuple(year_params)
    kpis = _cached_api_json("kpis/summary", params_tuple, token)
    if not kpis:
        st.error("Erreur API summary : données indisponibles")
        st.stop()

    monthly_data = _cached_api_json("kpis/monthly", params_tuple, token)
    boutique_data = _cached_api_json("kpis/by_boutique", params_tuple, token)
    paiement_data = _cached_api_json("kpis/by_paiement", params_tuple, token)

    monthly_df = pd.DataFrame(monthly_data)
    month_labels = {1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Juin", 7: "Juil", 8: "Aoû", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Déc"}
    if not monthly_df.empty and "annee" in monthly_df.columns and "mois" in monthly_df.columns:
        monthly_df["annee"] = monthly_df["annee"].astype(int)
        monthly_df["mois"] = monthly_df["mois"].astype(int)
        if selected_year != "Tout":
            monthly_df = monthly_df[monthly_df["annee"] == selected_year]
        monthly_df = monthly_df.sort_values(["annee", "mois"])
        monthly_df["mois_label"] = monthly_df["mois"].map(month_labels)
    else:
        monthly_df = pd.DataFrame()

    render_kpi_cards(kpis, monthly_data, year=selected_year)

    if not monthly_df.empty:
        fig_line = px.line(
            monthly_df,
            x="mois_label",
            y="ca_total",
            color="annee",
            markers=True,
            template="plotly_dark",
            title="CA mensuel par année",
            category_orders={"mois_label": [month_labels[i] for i in range(1, 13)]},
        )
        fig_line.update_layout(yaxis=dict(tickformat=","), margin=dict(t=50, b=50, l=60, r=20))
        st.plotly_chart(fig_line, use_container_width=True)

    _render_executive_summary(kpis, pd.DataFrame(monthly_data), selected_boutique, selected_year)

    boutique_df = pd.DataFrame(boutique_data)
    paiement_df = pd.DataFrame(paiement_data)

    # --- 1 SEUL appel Gemini pour tous les insights (batch + cache) ---
    specs = _collect_specs(monthly_df=monthly_df, boutique_df=boutique_df, paiement_df=paiement_df)
    insights: dict[str, str] = {}
    if specs:
        try:
            specs_tuple = tuple(
                json.dumps({"key": s["key"], "context": s["context"], "data": s["data"]}, sort_keys=True, ensure_ascii=False)
                for s in specs
            )
            insights = _cached_batch_insights(specs_tuple)
        except Exception as exc:
            st.warning(f"💡 Insights IA temporairement indisponibles ({exc}).")

    # --- Rendu des graphiques + insights ---
    if insights.get("monthly"):
        st.info(insights["monthly"])

    if not boutique_df.empty:
        fig_boutique = px.bar(
            boutique_df,
            x="ca_total",
            y="id_boutique",
            orientation="h",
            template="plotly_dark",
            title="CA par boutique",
        )
        st.plotly_chart(fig_boutique, use_container_width=True)
        if insights.get("boutique"):
            st.info(insights["boutique"])

    if not paiement_df.empty:
        fig_paiement = px.pie(
            paiement_df,
            names="mode_paiement",
            values="ca_total",
            template="plotly_dark",
            title="CA par mode de paiement",
        )
        st.plotly_chart(fig_paiement, use_container_width=True)
        if insights.get("paiement"):
            st.info(insights["paiement"])

    st.markdown("### Export")
    dashboard_pdf = _build_dashboard_pdf(
        kpis=kpis,
        monthly_df=monthly_df,
        boutique_df=boutique_df,
        paiement_df=paiement_df,
        insights=insights,
        year=str(selected_year),
        boutique=selected_boutique,
    )
    st.download_button(
        "Télécharger le dashboard en PDF",
        data=dashboard_pdf,
        file_name=f"sid-dream-dashboard-{datetime.now():%Y%m%d-%H%M}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

except Exception as e:
    st.error(f"Erreur de connexion : {e}")
