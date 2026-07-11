import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.title("Analyse des performances")

token = st.session_state.get("token")
if not token:
    st.error("Veuillez vous connecter")
    st.stop()

API_URL = "http://127.0.0.1:8000"
headers = {"Authorization": f"Bearer {token}"}

try:
    summary_resp = requests.get(f"{API_URL}/kpis/summary", headers=headers, timeout=10)
    if summary_resp.status_code == 200:
        summary = summary_resp.json()

        st.subheader("Résumé global")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("CA Total", f"{summary.get('ca_total', 0):,.0f} FCFA")
        col2.metric("Nb Transactions", f"{summary.get('nb_transactions', 0):,}")
        col3.metric("Panier Moyen", f"{summary.get('panier_moyen', 0):,.2f} FCFA")
        col4.metric("Clients Uniques", f"{summary.get('nb_clients_uniques', 0):,}")
        col5.metric("Produits Uniques", f"{summary.get('nb_produits_uniques', 0):,}")
    elif summary_resp.status_code == 401:
        st.error("Votre session a expiré. Veuillez vous reconnecter.")
        st.stop()
    else:
        st.error(f"Erreur API summary : {summary_resp.status_code}")
        st.stop()

    st.markdown("---")

    monthly_resp = requests.get(f"{API_URL}/kpis/monthly", headers=headers, timeout=10)
    if monthly_resp.status_code == 200:
        monthly_data = monthly_resp.json()
        monthly_df = pd.DataFrame(monthly_data)
        if not monthly_df.empty:
            monthly_df["mois_label"] = monthly_df.apply(
                lambda row: f"{int(row['mois']):02d}/{int(row['annee'])}", axis=1
            )
            fig_monthly = px.line(
                monthly_df,
                x="mois_label",
                y="ca_total",
                markers=True,
                labels={"mois_label": "Mois", "ca_total": "CA total (FCFA)"},
                title="CA par mois",
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
    elif monthly_resp.status_code == 401:
        st.error("Votre session a expiré. Veuillez vous reconnecter.")
    else:
        st.error(f"Erreur API monthly : {monthly_resp.status_code}")

    st.markdown("---")

    boutique_resp = requests.get(f"{API_URL}/kpis/by_boutique", headers=headers, timeout=10)
    if boutique_resp.status_code == 200:
        boutique_data = boutique_resp.json()
        boutique_df = pd.DataFrame(boutique_data)
        if not boutique_df.empty:
            fig_boutique = px.bar(
                boutique_df,
                x="ca_total",
                y="id_boutique",
                orientation="h",
                text="ca_total",
                labels={"id_boutique": "Boutique", "ca_total": "CA total (FCFA)"},
                title="CA par boutique",
            )
            fig_boutique.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
            st.plotly_chart(fig_boutique, use_container_width=True)
    elif boutique_resp.status_code == 401:
        st.error("Votre session a expiré. Veuillez vous reconnecter.")
    else:
        st.error(f"Erreur API by_boutique : {boutique_resp.status_code}")

    st.markdown("---")

    paiement_resp = requests.get(f"{API_URL}/kpis/by_paiement", headers=headers, timeout=10)
    if paiement_resp.status_code == 200:
        paiement_data = paiement_resp.json()
        paiement_df = pd.DataFrame(paiement_data)
        if not paiement_df.empty:
            fig_paiement = px.pie(
                paiement_df,
                names="mode_paiement",
                values="ca_total",
                title="CA par mode de paiement",
            )
            st.plotly_chart(fig_paiement, use_container_width=True)
    elif paiement_resp.status_code == 401:
        st.error("Votre session a expiré. Veuillez vous reconnecter.")
    else:
        st.error(f"Erreur API by_paiement : {paiement_resp.status_code}")
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
