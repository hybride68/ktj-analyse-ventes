import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.title("Segmentation RFM")

token = st.session_state.get("token")
if not token:
    st.error("Veuillez vous connecter")
    st.stop()

API_URL = "http://127.0.0.1:8000"

try:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/rfm/segments", headers=headers, timeout=5)
    if resp.status_code == 200:
        data = resp.json()

        # Ensure DataFrame
        df = pd.DataFrame(data)

        # Metrics for segments
        vip = df[df["segment"].str.lower().str.contains("vip", na=False)]
        fideles = df[df["segment"].str.contains("Fid", na=False)]
        a_risque = df[df["segment"].str.contains("risque", na=False)]

        col1, col2, col3 = st.columns(3)

        col1.metric("VIP - Nb clients", int(vip["nb_clients"].sum()) if not vip.empty else 0)
        col2.metric("Fidèles - Nb clients", int(fideles["nb_clients"].sum()) if not fideles.empty else 0)
        col3.metric("À risque - Nb clients", int(a_risque["nb_clients"].sum()) if not a_risque.empty else 0)

        # Bar chart - montant_moyen par segment
        if "montant_moyen" in df.columns:
            fig_bar = px.bar(
                df,
                x="segment",
                y="montant_moyen",
                title="Montant moyen par segment",
                labels={"montant_moyen": "Montant moyen (FCFA)", "segment": "Segment"},
                text=df["montant_moyen"].map(lambda x: f"{x:,.0f}" if pd.notnull(x) else "0"),
            )
            fig_bar.update_layout(yaxis_tickformat=",")
            st.plotly_chart(fig_bar, use_container_width=True)

        # Pie chart - répartition clients
        if "nb_clients" in df.columns:
            fig_pie = px.pie(
                df,
                names="segment",
                values="nb_clients",
                title="Répartition des clients par segment",
                hole=0.3,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    elif resp.status_code == 401:
        st.error("Votre session a expiré. Veuillez vous reconnecter.")
    else:
        st.error(f"Erreur API : {resp.status_code}")
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
