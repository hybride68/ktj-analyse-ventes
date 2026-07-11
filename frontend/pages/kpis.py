import requests
import streamlit as st

st.title("Vue Générale — KPIs")

token = st.session_state.get("token")
if not token:
    st.error("Veuillez vous connecter")
    st.stop()

API_URL = "http://127.0.0.1:8000"

try:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_URL}/kpis/summary",
        headers=headers,
        timeout=5,
    )
    if response.status_code == 200:
        data = response.json()

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "CA Total",
            f"{data['ca_total']:,.0f} FCFA",
        )
        col2.metric(
            "Nb Transactions",
            f"{data['nb_transactions']:,}",
        )
        col3.metric(
            "Panier Moyen",
            f"{data['panier_moyen']:,.2f} FCFA",
        )
        col4.metric(
            "Clients Uniques",
            f"{data['nb_clients_uniques']:,}",
        )
        col5.metric(
            "Produits Uniques",
            f"{data['nb_produits_uniques']:,}",
        )
    elif response.status_code == 401:
        st.error("Votre session a expiré. Veuillez vous reconnecter.")
    else:
        st.error(f"Erreur API : {response.status_code}")
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
