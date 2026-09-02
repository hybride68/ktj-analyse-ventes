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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from frontend.theme import apply_theme, render_sidebar, render_account_card
from backend.gemini import generate_insight

if not st.session_state.get("app_shell_active", False):
    st.set_page_config(page_title="SID-Dream - Analyse Prescriptive", layout="wide", initial_sidebar_state="expanded")
    apply_theme()
    render_sidebar("Prescriptive")
else:
    apply_theme()
    render_sidebar("Prescriptive")

render_account_card()
st.title("SID-Dream — Analyse Prescriptive")

API_URL = get_api_url()
token = st.session_state.get("token")
if not token:
    st.error("Veuillez vous connecter")
    st.stop()

headers = {"Authorization": f"Bearer {token}"}

segments_resp = requests.get(f"{API_URL}/rfm/segments", headers=headers, timeout=10)
segments_df = pd.DataFrame(segments_resp.json()) if segments_resp.status_code == 200 else pd.DataFrame()

clients_resp = requests.get(f"{API_URL}/rfm/clients", headers=headers, timeout=10)
clients_df = pd.DataFrame(clients_resp.json()) if clients_resp.status_code == 200 else pd.DataFrame()

segment_colors = {
    "Occasionnels": "#5B6CF6",
    "Fidèles": "#2C7BE5",
    "A risque": "#F04452",
    "VIP": "#34D399",
}


def _build_recommendations(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Construit les actions à partir des indicateurs RFM réellement disponibles."""
    if dataframe.empty:
        return pd.DataFrame(columns=["segment", "action", "priorité"])

    working = dataframe.copy()
    metric_columns = ["recence_moyenne", "frequence_moyenne", "montant_moyen"]
    for column in metric_columns:
        working[column] = pd.to_numeric(working[column], errors="coerce").fillna(0)

    recency_reference = working["recence_moyenne"].median()
    frequency_reference = working["frequence_moyenne"].median()
    amount_reference = working["montant_moyen"].median()
    recommendations = []

    for _, row in working.iterrows():
        segment = str(row.get("segment") or "Non classé")
        recency = row["recence_moyenne"]
        frequency = row["frequence_moyenne"]
        amount = row["montant_moyen"]

        if segment == "VIP":
            action = "Maintenir une fidélisation premium et proposer des offres exclusives."
        elif segment == "Fidèles":
            action = "Développer la fréquence d'achat avec des offres personnalisées."
        elif segment == "Occasionnels":
            action = "Lancer une campagne ciblée pour augmenter la fréquence d'achat."
        elif segment == "A risque":
            action = "Déclencher une relance prioritaire avec une remise personnalisée."
        else:
            action = "Tester une campagne ciblée et suivre son impact sur les achats."

        signals = []
        if recency_reference and recency > recency_reference * 1.5:
            signals.append("récence élevée")
        if frequency_reference and frequency < frequency_reference * 0.75:
            signals.append("fréquence faible")
        if amount_reference and amount > amount_reference * 1.5:
            signals.append("montant élevé")
        if signals:
            action += f" Indicateurs détectés : {', '.join(signals)}."

        priority = "Haute" if segment == "A risque" or recency > recency_reference * 1.5 else "Moyenne"
        if segment == "VIP" and amount > amount_reference:
            priority = "Haute"

        recommendations.append({
            "segment": segment,
            "clients": int(row.get("nb_clients", 0)),
            "récence moyenne": round(recency, 2),
            "fréquence moyenne": round(frequency, 2),
            "montant moyen": round(amount, 2),
            "action": action,
            "priorité": priority,
        })

    return pd.DataFrame(recommendations).sort_values(
        ["priorité", "clients"], ascending=[True, False], key=lambda values: values.map({"Haute": 0, "Moyenne": 1}).fillna(2) if values.name == "priorité" else values
    )

if not segments_df.empty:
    segments_df = segments_df.copy()
    segments_df["ca_total_segment"] = segments_df["nb_clients"] * segments_df["montant_moyen"]
    segments_df["part_ca_total"] = segments_df["ca_total_segment"] / segments_df["ca_total_segment"].sum() if segments_df["ca_total_segment"].sum() else 0

    st.markdown("### Segments RFM")
    segment_cards = ["VIP", "Fidèles", "Occasionnels", "A risque"]
    cols = st.columns(4)
    for col, segment_name in zip(cols, segment_cards):
        row = segments_df[segments_df["segment"] == segment_name]
        if not row.empty:
            row = row.iloc[0]
            col.metric(
                segment_name,
                f"{int(row['nb_clients']):,} clients",
                f"Montant moyen {int(row['montant_moyen']):,} FCFA",
            )
        else:
            col.metric(segment_name, "0 clients", "Montant moyen 0 FCFA")

    fig_ca_share = px.pie(
        segments_df,
        names="segment",
        values="ca_total_segment",
        color="segment",
        color_discrete_map=segment_colors,
        template="plotly_dark",
        title="Part des segments dans le CA total",
    )

    fig_clients = px.pie(
        segments_df,
        names="segment",
        values="nb_clients",
        color="segment",
        color_discrete_map=segment_colors,
        template="plotly_dark",
        title="Répartition des clients par segment",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_ca_share, use_container_width=True)
    with col2:
        st.plotly_chart(fig_clients, use_container_width=True)

    fig_bar = px.bar(
        segments_df,
        x="segment",
        y="montant_moyen",
        color="segment",
        color_discrete_map=segment_colors,
        template="plotly_dark",
        title="Montant moyen par segment",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

if not clients_df.empty:
    scatter_df = clients_df.copy()
    scatter_df["segment"] = scatter_df["segment"].fillna("Non classé")
    scatter_df["recence"] = pd.to_numeric(scatter_df["recence"], errors="coerce")
    scatter_df["montant"] = pd.to_numeric(scatter_df["montant"], errors="coerce")
    scatter_df["frequence"] = pd.to_numeric(scatter_df["frequence"], errors="coerce")
    scatter_df = scatter_df.dropna(subset=["recence", "montant", "frequence"])

    st.markdown(
        """
        **Lecture simple** : chaque point représente un client.  
        - **Axe horizontal (Récence)** : plus la valeur est faible, plus le client a acheté récemment.  
        - **Axe vertical (Montant)** : plus la valeur est haute, plus le client dépense.  
        - **Couleur** : indique le segment RFM du client.  
        Les clients les plus intéressants sont généralement en haut et à gauche du graphique.
        """
    )

    fig_scatter = px.scatter(
        scatter_df,
        x="recence",
        y="montant",
        color="segment",
        color_discrete_map={**segment_colors, "Non classé": "#AAB4C8"},
        size="frequence",
        hover_name="nom",
        hover_data={"recence": True, "montant": True, "frequence": True, "segment": True},
        template="plotly_dark",
        title="Récence vs Montant (chaque point = un client)",
    )
    fig_scatter.update_traces(marker=dict(opacity=0.8))
    fig_scatter.update_layout(
        xaxis_title="Récence (faible = client récent)",
        yaxis_title="Montant dépensé (FCFA)",
        legend_title="Segment",
    )
    fig_scatter.update_xaxes(autorange="reversed")
    st.plotly_chart(fig_scatter, use_container_width=True)

st.subheader("Recommandations d’action")
recommendations = _build_recommendations(segments_df)

st.subheader("Tableau de recommandations")
st.dataframe(recommendations, use_container_width=True, hide_index=True)

try:
    insight = generate_insight(segments_df.to_dict("records"), "Recommandations d'action par segment RFM")
    st.info(insight)
except Exception:
    st.caption("Insight IA indisponible pour le moment.")
