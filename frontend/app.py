import os

import pandas as pd
import requests
import streamlit as st

try:
    from frontend.api_config import get_api_url
except ImportError:
    from api_config import get_api_url

st.set_page_config(page_title="SID-Dream", page_icon="✨", initial_sidebar_state="collapsed")

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
WEEKLY_SALES_FILE = os.path.join(DATA_DIR, 'weekly_sales.csv')


def _load_weekly_sales() -> pd.DataFrame:
    if os.path.exists(WEEKLY_SALES_FILE):
        try:
            df = pd.read_csv(WEEKLY_SALES_FILE)
            if 'week_start' in df.columns and 'ca_vente' in df.columns:
                return df[['week_start', 'ca_vente']]
        except Exception:
            pass
    return pd.DataFrame(columns=['week_start', 'ca_vente'])


def _save_weekly_sales(df: pd.DataFrame) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(WEEKLY_SALES_FILE, index=False)

API_URL = get_api_url()

if "token" not in st.session_state:
    st.session_state["token"] = None
if "profil" not in st.session_state:
    st.session_state["profil"] = None


def login():
    st.title("SID-Dream")
    st.markdown(
        "Bienvenue dans SID-Dream, la plateforme d'analyse décisionnelle pour une PME du secteur électronique et électroménager."
    )

    with st.form("login_form"):
        email = st.text_input("Email")
        mot_de_passe = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")

        if submit:
            if not email or not mot_de_passe:
                st.error("Veuillez remplir tous les champs")
                return

            try:
                response = requests.post(
                    f"{API_URL}/auth/login",
                    json={"email": email, "mot_de_passe": mot_de_passe},
                    timeout=5,
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state["token"] = data.get("access_token")
                    st.session_state["profil"] = email
                    st.success("Connexion réussie !")
                    st.info("Utilisez le menu de pages en haut à gauche pour accéder aux sections du dashboard SID-Dream.")
                    st.rerun()
                else:
                    st.error("Email ou mot de passe incorrect")
            except Exception as e:
                st.error(f"Erreur de connexion : {e}")


def dashboard():
    st.markdown(
        "# SID-Dream"
        "\n#### Plateforme d’analyse décisionnelle haute valeur pour PME"
    )
    st.markdown(
        "Bienvenue **{}** — accédez rapidement aux analyses stratégiques et aux données opérationnelles.".format(st.session_state['profil'])
    )

    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("### Visualisation des données et KPI en temps réel")
            st.markdown(
                "- Analyse descriptive des ventes et du CA"
                "\n- Analyse diagnostique des tendances et des produits"
                "\n- Analyse prédictive basée sur les 12 dernières semaines de 2025"
                "\n- Recommandations prescriptives par segment client"
            )
        with col2:
            st.info("Utilisez le menu en haut à gauche pour naviguer entre les modules.")

    st.markdown("---")
    st.subheader("Saisie des ventes hebdomadaires")
    st.markdown(
        "Importez ou modifiez vos ventes hebdomadaires pour alimenter la base de données et recalibrer le modèle."
    )
    weekly_sales = _load_weekly_sales()
    uploaded = st.file_uploader(
        "Importer un CSV de ventes hebdomadaires (colonnes : week_start, ca_vente)",
        type=["csv"],
    )
    if uploaded is not None:
        try:
            uploaded_df = pd.read_csv(uploaded)
            if 'week_start' in uploaded_df.columns and 'ca_vente' in uploaded_df.columns:
                uploaded_df = uploaded_df[['week_start', 'ca_vente']]
                uploaded_df['ca_vente'] = pd.to_numeric(uploaded_df['ca_vente'], errors='coerce').fillna(0)
                weekly_sales = uploaded_df
                st.success("Ventes hebdomadaires importées avec succès.")
            else:
                st.error("Le fichier doit contenir les colonnes week_start et ca_vente.")
        except Exception as exc:
            st.error(f"Impossible de lire le fichier CSV : {exc}")

    try:
        editor = getattr(st, "data_editor", None) or getattr(st, "experimental_data_editor", None)
        if editor:
            edited = editor(weekly_sales, num_rows="dynamic")
        else:
            edited = weekly_sales
            st.dataframe(weekly_sales)
    except Exception:
        edited = weekly_sales
        st.dataframe(weekly_sales)

    if st.button("Enregistrer les ventes hebdomadaires"):
        try:
            _save_weekly_sales(edited)
            st.success("Données enregistrées. Elles seront utilisées pour recalibrer le modèle et alimenter le dashboard.")
        except Exception as exc:
            st.error(f"Erreur lors de l'enregistrement : {exc}")

    if st.sidebar.button("Déconnexion"):
        st.session_state["token"] = None
        st.session_state["profil"] = None
        st.rerun()

    st.sidebar.markdown("### SID-Dream")
    st.sidebar.write("Dashboard décisionnel pour la performance commerciale et la stratégie magasin.")
    st.sidebar.write("\n---\n")


if st.session_state["token"]:
    dashboard()
else:
    login()
