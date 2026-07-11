import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("Prévisions des ventes")

token = st.session_state.get("token")
if not token:
    st.error("Veuillez vous connecter")
    st.stop()

API_URL = "http://127.0.0.1:8000"

try:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/previsions/monthly", headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        # Expecting a list of dicts with keys including 'mois' and the ca fields
        df = pd.DataFrame(data)

        if 'mois' in df.columns:
            df['mois'] = pd.to_datetime(df['mois'], errors='coerce')
            df = df[df['mois'] > pd.Timestamp('2024-12-31')]
            df = df.sort_values('mois')
            df = df.set_index('mois')
            df = df.resample('ME').mean(numeric_only=True).reset_index()
            df['mois_str'] = df['mois'].dt.strftime('%b %Y')
            df['mois_str'] = df['mois_str'].str.replace('Jan', 'Jan').str.replace('Feb', 'Fév').str.replace('Mar', 'Mar').str.replace('Apr', 'Avr').str.replace('May', 'Mai').str.replace('Jun', 'Juin').str.replace('Jul', 'Juil').str.replace('Aug', 'Aoû').str.replace('Sep', 'Sep').str.replace('Oct', 'Oct').str.replace('Nov', 'Nov').str.replace('Dec', 'Déc')
        else:
            df['mois_str'] = df.index.astype(str)

        if df.empty:
            st.info("Aucune donnée de prévision disponible.")
        else:
            fig = go.Figure()
            if 'ca_prevision_moyenne' in df.columns:
                fig.add_trace(go.Bar(x=df['mois_str'], y=df['ca_prevision_moyenne'],
                                     name='CA prévision moyenne',
                                     marker=dict(color='royalblue')))
                fig.update_traces(text=df['ca_prevision_moyenne'].map(lambda x: f"{x:,.0f} FCFA"), textposition='outside')
            if 'ca_min_moyenne' in df.columns:
                fig.add_trace(go.Scatter(x=df['mois_str'], y=df['ca_min_moyenne'],
                                         mode='lines+markers', name='CA min moyenne',
                                         line=dict(color='red', dash='dot')))
            if 'ca_max_moyenne' in df.columns:
                fig.add_trace(go.Scatter(x=df['mois_str'], y=df['ca_max_moyenne'],
                                         mode='lines+markers', name='CA max moyenne',
                                         line=dict(color='green', dash='dot')))

            fig.update_layout(title='Prévisions mensuelles du CA',
                              xaxis_title='Mois',
                              yaxis_title='CA (FCFA)',
                              template='plotly_white',
                              barmode='group')

            st.plotly_chart(fig, use_container_width=True)
    elif resp.status_code == 401:
        st.error("Votre session a expiré. Veuillez vous reconnecter.")
    else:
        st.error(f"Erreur API : {resp.status_code}")
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
