import os
import runpy

import pandas as pd
import requests
import streamlit as st

try:
    from frontend.api_config import get_api_url
    from frontend.theme import apply_theme, render_sidebar
except ImportError:
    from api_config import get_api_url
    from theme import apply_theme, render_sidebar

st.set_page_config(page_title="SID-Dream", page_icon="✨", initial_sidebar_state="expanded")
if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "app"
if "app_shell_active" not in st.session_state:
    st.session_state["app_shell_active"] = True

apply_theme(hide_sidebar=not bool(st.session_state.get("token")))

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
if "role" not in st.session_state:
    st.session_state["role"] = None


def login():
    left_col, right_col = st.columns([1.55, 0.9], vertical_alignment="center")

    with left_col:
        st.markdown(
            """
            <div class='login-copy-hero'>
                <div class='login-brand'>
                    <span>▥</span>
                    <div>
                        <strong>SID-Dream</strong>
                        <small>Système d'Information Décisionnel</small>
                    </div>
                </div>
                <h2>Bienvenue<br><em>dans votre espace.</em></h2>
                <p>Analysez vos ventes, comprenez vos clients et prenez de meilleures décisions grâce aux données.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown("<div class='login-page-marker'></div>", unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            st.markdown(
                """
                <div class='login-panel-heading'>
                    <h3>Connexion</h3>
                    <p>Accédez à votre espace d'analyse</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            email = st.text_input("Adresse e-mail", key="login_email")
            mot_de_passe = st.text_input("Mot de passe", type="password", key="login_password")
            submit = st.form_submit_button("Se connecter", use_container_width=True)

        if submit:
            if not email or not mot_de_passe:
                st.error("Veuillez remplir tous les champs")
            else:
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
                        st.session_state["role"] = data.get("role", "user")
                        st.success("Connexion réussie !")
                        st.info("Utilisez le menu de pages en haut à gauche pour accéder aux sections du dashboard SID-Dream.")
                        st.rerun()
                    else:
                        st.error("Email ou mot de passe incorrect")
                except Exception as e:
                    st.error(f"Erreur de connexion : {e}")


def dashboard():
    render_sidebar("app")

    st.markdown(
        "<h1>Bonjour, <span class='welcome-email'>{}</span></h1>".format(st.session_state.get('profil', 'utilisateur')),
        unsafe_allow_html=True,
    )
    st.markdown("<p class='welcome-subtitle'>Votre performance, en un regard</p>", unsafe_allow_html=True)

    st.markdown("<div class='welcome-section-title'>Bienvenue dans SID-Dream</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='welcome-panel'>
            <p>Accédez rapidement à l'analyse descriptive, au diagnostic, aux prévisions et aux recommandations stratégiques.</p>
            <p>Utilisez la barre latérale pour naviguer entre les pages de votre tableau de bord et piloter votre performance commerciale en temps réel.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    quick_cols = st.columns(3)
    with quick_cols[0]:
        st.markdown("<div class='welcome-feature'>Analyse descriptive</div>", unsafe_allow_html=True)
        st.caption("Suivi des performances, volumes et rentabilité.")
    with quick_cols[1]:
        st.markdown("<div class='welcome-feature'>Diagnostic</div>", unsafe_allow_html=True)
        st.caption("Identification des écarts, tendances et opportunités.")
    with quick_cols[2]:
        st.markdown("<div class='welcome-feature'>Prédictions</div>", unsafe_allow_html=True)
        st.caption("Prévisions commerciales et simulation de scénarios.")

    if st.sidebar.button("Déconnexion"):
        st.session_state["token"] = None
        st.session_state["profil"] = None
        st.session_state["role"] = None
        st.rerun()


PAGE_FILES = {
    "app": None,
    "Descriptive": os.path.join(os.path.dirname(__file__), "pages", "1_Descriptive.py"),
    "Diagnostique": os.path.join(os.path.dirname(__file__), "pages", "2_Diagnostique.py"),
    "Predictive": os.path.join(os.path.dirname(__file__), "pages", "3_Predictive.py"),
    "Prescriptive": os.path.join(os.path.dirname(__file__), "pages", "4_Prescriptive.py"),
    "Gestion Utilisateurs": os.path.join(os.path.dirname(__file__), "pages", "5_Gestion_Utilisateurs.py"),
}


if st.session_state["token"]:
    selected_page = st.session_state.get("selected_page", "app")
    if selected_page == "app":
        dashboard()
    else:
        target = PAGE_FILES.get(selected_page)
        if target and os.path.exists(target):
            st.session_state["app_shell_active"] = True
            runpy.run_path(target, run_name="__main__")
        else:
            dashboard()
else:
    login()
