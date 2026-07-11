import requests
import streamlit as st

st.set_page_config(page_title="Projet PME", page_icon="📊")

API_URL = "http://127.0.0.1:8000"

if "token" not in st.session_state:
    st.session_state["token"] = None
if "profil" not in st.session_state:
    st.session_state["profil"] = None


def login():
    st.title("Connexion - Tableau de bord PME")
    st.markdown(
        "Application d'analyse décisionnelle pour une PME du secteur électronique et électroménager."
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
                    st.success("Connexion réussie!")
                    st.rerun()
                else:
                    st.error("Email ou mot de passe incorrect")
            except Exception as e:
                st.error(f"Erreur de connexion : {e}")


def dashboard():
    st.title("Tableau de bord PME")
    st.markdown(
        f"Bienvenue {st.session_state['profil']} ! Vous êtes connecté."
    )

    if st.sidebar.button("Déconnexion"):
        st.session_state["token"] = None
        st.session_state["profil"] = None
        st.rerun()

    st.sidebar.info("Application d'analyse décisionnelle pour une PME.")


if st.session_state["token"]:
    dashboard()
else:
    login()
