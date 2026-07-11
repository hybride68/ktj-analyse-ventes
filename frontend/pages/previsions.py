import streamlit as st
import requests

st.title("Prévisions de ventes")

try:
    response = requests.get("http://127.0.0.1:8000/previsions/", timeout=5)
    if response.ok:
        data = response.json()
        st.write(f"Période : {data['periode']}")
        st.dataframe(data["previsions"])
    else:
        st.warning("API indisponible")
except Exception as e:
    st.warning(f"Connexion à l'API impossible : {e}")
