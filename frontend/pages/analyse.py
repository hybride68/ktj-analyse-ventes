import streamlit as st

st.title("Analyse métier")
st.write("Cette page permet d'observer l'évolution du chiffre d'affaires, la performance par boutique et la saisonnalité.")

st.bar_chart({"CA mensuel": [1200000, 1350000, 1500000, 1650000, 1800000]})
