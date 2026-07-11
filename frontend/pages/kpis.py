import streamlit as st
import requests

st.title("Vue générale")

try:
    response = requests.get("http://127.0.0.1:8000/kpis/", timeout=5)
    if response.ok:
        data = response.json()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("CA total", f"{data['ca_total']:,} FCFA")
        col2.metric("Transactions", f"{data['nb_transactions']:,}")
        col3.metric("Panier moyen", f"{data['panier_moyen']:.0f} FCFA")
        col4.metric("Évolution mois", f"{data['evolution_mois']:+.1f}%")
    else:
        st.warning("API indisponible")
except Exception as e:
    st.warning(f"Connexion à l'API impossible : {e}")
