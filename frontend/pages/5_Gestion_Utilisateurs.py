import os
import sys

import requests
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from frontend.theme import apply_theme, render_sidebar, render_account_card

try:
    from frontend.api_config import get_api_url
except ImportError:
    from api_config import get_api_url

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

if not st.session_state.get("app_shell_active", False):
    st.set_page_config(page_title="SID-Dream - Gestion Utilisateurs", layout="wide", initial_sidebar_state="expanded")
    apply_theme()
    render_sidebar("Gestion Utilisateurs")
else:
    apply_theme()
    render_sidebar("Gestion Utilisateurs")

st.title("SID-Dream — Gestion des utilisateurs")

API_URL = get_api_url()
token = st.session_state.get("token")
if not token:
    st.error("Veuillez vous connecter")
    st.stop()

headers = {"Authorization": f"Bearer {token}"}
# Vérifier que l'utilisateur courant est admin
try:
    me_resp = requests.get(f"{API_URL}/auth/me", headers=headers, timeout=10)
    if me_resp.status_code != 200:
        st.error("Impossible de vérifier le profil utilisateur. Accès refusé.")
        st.stop()
    me = me_resp.json()
    if me.get("role") != "admin":
        st.error("Accès réservé aux administrateurs")
        st.stop()
except Exception:
    st.error("Impossible de contacter l'API d'authentification.")
    st.stop()

st.sidebar.info("Page réservée aux administrateurs : création et suppression d'utilisateurs (consultation seulement).")

st.subheader("Importer des données")
st.caption("Les fichiers CSV sont contrôlés avant insertion. Les lignes invalides ou déjà présentes sont ignorées.")
dataset_labels = {
    "ventes": "Ventes",
    "produits": "Produits",
    "clients": "Clients",
    "boutiques": "Boutiques",
}
selected_dataset = st.selectbox("Type de données", list(dataset_labels), format_func=dataset_labels.get)
uploaded_file = st.file_uploader("Fichier CSV", type=["csv"])
if uploaded_file is not None and st.button("Valider et importer", key="import_data"):
    try:
        import_response = requests.post(
            f"{API_URL}/imports/{selected_dataset}",
            files={"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")},
            headers=headers,
            timeout=60,
        )
        if import_response.status_code == 200:
            report = import_response.json()
            st.success(f"Import terminé : {report['lignes_inserees']} ligne(s) insérée(s).")
            st.info(f"{report['lignes_rejetees']} ligne(s) rejetée(s), dont {report['total_erreurs']} erreur(s).")
            if report.get("erreurs"):
                st.dataframe(pd.DataFrame(report["erreurs"]), use_container_width=True)
        else:
            try:
                error_message = import_response.json().get("detail", import_response.text)
            except ValueError:
                error_message = import_response.text
            st.error(f"Import impossible : {error_message}")
    except requests.RequestException as exc:
        st.error(f"Erreur de connexion pendant l'import : {exc}")

with st.form("create_user_form"):
    st.subheader("Créer un utilisateur (lecture seule)")
    nom = st.text_input("Nom")
    email = st.text_input("Email")
    mot_de_passe = st.text_input("Mot de passe", type="password")
    is_active = st.checkbox("Compte actif", value=True)
    submitted = st.form_submit_button("Créer l’utilisateur")

    if submitted:
        if not nom or not email or not mot_de_passe:
            st.error("Nom, email et mot de passe sont obligatoires")
        else:
            # Les comptes créés depuis cette page sont des utilisateurs standards.
            payload = {
                "nom": nom,
                "email": email,
                "mot_de_passe": mot_de_passe,
                "profil": "utilisateur",
                "role": "user",
                "boutique_id": None,
                "is_active": is_active,
            }
            try:
                response = requests.post(f"{API_URL}/auth/users", json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    st.success("Utilisateur créé avec succès")
                    if hasattr(st, "experimental_rerun"):
                        try:
                            st.experimental_rerun()
                        except Exception:
                            st.info("Veuillez rafraîchir la page pour appliquer les changements.")
                    else:
                        st.info("Veuillez rafraîchir la page pour appliquer les changements.")
                else:
                    try:
                        err = response.json().get("detail", response.text)
                    except Exception:
                        err = response.text
                    st.error(f"Erreur lors de la création : {err}")
            except Exception as exc:
                st.error(f"Erreur : {exc}")

st.markdown("---")

st.subheader("Utilisateurs ayant accès au dashboard")
try:
    users_resp = requests.get(f"{API_URL}/auth/users", headers=headers, timeout=10)
    users = []
    if users_resp.status_code == 200:
        try:
            users = users_resp.json()
        except ValueError:
            st.error("Réponse API invalide : le serveur n'a pas renvoyé du JSON.")
            st.write(users_resp.text)
    else:
        try:
            error_body = users_resp.json().get("detail", users_resp.text)
        except ValueError:
            error_body = users_resp.text or f"Statut HTTP {users_resp.status_code}"
        st.error(f"Impossible de récupérer la liste des utilisateurs : {error_body}")

    if users:
        st.markdown("### Utilisateurs")
        for user in users:
            cols = st.columns([3, 3, 1, 1])
            cols[0].markdown(f"**{user['nom']}**")
            cols[1].markdown(f"{user['email']}")
            cols[2].markdown(f"Actif : {'Oui' if user.get('is_active') else 'Non'}")
            # suppression (admin uniquement) — protection contre suppression self
            if user['id'] != me.get('id'):
                if cols[3].button("Supprimer", key=f"del_{user['id']}"):
                    try:
                        resp = requests.delete(f"{API_URL}/auth/users/{user['id']}", headers=headers, timeout=10)
                        if resp.status_code in (200,204):
                            st.success("Utilisateur supprimé")
                            if hasattr(st, "experimental_rerun"):
                                try:
                                    st.experimental_rerun()
                                except Exception:
                                    st.info("Veuillez rafraîchir la page pour appliquer les changements.")
                            else:
                                st.info("Veuillez rafraîchir la page pour appliquer les changements.")
                        else:
                            try:
                                err = resp.json().get('detail', resp.text)
                            except Exception:
                                err = resp.text
                            st.error(f"Erreur suppression : {err}")
                    except Exception as exc:
                        st.error(f"Erreur lors de la suppression : {exc}")
            else:
                cols[3].write("Vous")
    elif users_resp.status_code == 200:
        st.info("Aucun utilisateur trouvé.")
except Exception as exc:
    st.error(f"Erreur : {exc}")

# --- Vue d'aperçu pour les responsables de boutique ---
st.markdown("---")
st.subheader("Historique des connexions (dernières 100)")
try:
    hist_resp = requests.get(f"{API_URL}/auth/login-history", headers=headers, timeout=10)
    if hist_resp.status_code == 200:
        try:
            history = hist_resp.json()
            if history:
                import pandas as _pd

                hist_df = _pd.DataFrame(history)
                hist_df = hist_df.rename(columns={
                    'email': 'Email',
                    'login_time': 'Heure connexion',
                    'ip_address': 'IP',
                    'user_agent': 'User-Agent'
                })
                st.dataframe(hist_df[['Email', 'Heure connexion', 'IP', 'User-Agent']], use_container_width=True)
            else:
                st.info('Aucun événement de connexion trouvé.')
        except ValueError:
            st.error('Réponse API invalide pour l\'historique.')
    else:
        st.error('Impossible de récupérer l\'historique des connexions.')
except Exception:
    st.error('Erreur lors de la récupération de l\'historique des connexions.')
