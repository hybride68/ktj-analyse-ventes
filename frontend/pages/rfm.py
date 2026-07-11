import streamlit as st
import requests

st.title("Segmentation RFM")

try:
    response = requests.get("http://127.0.0.1:8000/rfm/", timeout=5)
    if response.ok:
        segments = response.json()["segments"]
        st.dataframe(segments)
    else:
        st.warning("API indisponible")
except Exception as e:
    st.warning(f"Connexion à l'API impossible : {e}")
