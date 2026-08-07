from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String

try:
    from backend.database import Base
except ImportError:
    from database import Base


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    mot_de_passe = Column(String, nullable=False)
    profil = Column(String, nullable=False)
    role = Column(String, nullable=False, default="analyst")
    boutique_id = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    date_creation = Column(DateTime, nullable=False)


class Vente(Base):
    __tablename__ = "ventes"

    id_transaction = Column(String, primary_key=True, index=True)
    date_vente = Column(Date, nullable=False)
    id_boutique = Column(String, nullable=False)
    id_client = Column(String, nullable=True)
    telephone_client = Column(String, nullable=True)
    code_produit = Column(String, nullable=False)
    prix_unitaire_facture = Column(Float, nullable=False)
    quantite = Column(Integer, nullable=False)
    mode_paiement = Column(String, nullable=True)
    annee = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    trimestre = Column(Integer, nullable=False)
    montant = Column(Float, nullable=False)


class Produit(Base):
    __tablename__ = "produits"

    code_produit = Column(String, primary_key=True, index=True)
    designation = Column(String, nullable=False)
    categorie = Column(String, nullable=False)
    sous_categorie = Column(String, nullable=True)
    marque = Column(String, nullable=True)
    prix_achat = Column(Float, nullable=True)
    prix_vente = Column(Float, nullable=True)
    unite = Column(String, nullable=True)


class Client(Base):
    __tablename__ = "clients"

    id_client = Column(String, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=True)
    telephone = Column(String, nullable=True)
    region = Column(String, nullable=True)
    type_client = Column(String, nullable=True)
    statut = Column(String, nullable=True)


class Boutique(Base):
    __tablename__ = "boutiques"

    id_boutique = Column(String, primary_key=True, index=True)
    nom_boutique = Column(String, nullable=False)
    ville = Column(String, nullable=True)
    region = Column(String, nullable=True)
    responsable = Column(String, nullable=True)
    nb_employes = Column(Integer, nullable=True)


class SegmentRFM(Base):
    __tablename__ = "segments_rfm"

    id = Column(Integer, primary_key=True, index=True)
    id_client = Column(String, nullable=False)
    recence = Column(Integer, nullable=True)
    frequence = Column(Integer, nullable=True)
    montant = Column(Float, nullable=True)
    segment = Column(String, nullable=False)
    date_calcul = Column(Date, nullable=True)


class Prevision(Base):
    __tablename__ = "previsions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    boutique_id = Column(String, nullable=True)
    ca_prevision = Column(Float, nullable=False)
    ca_min = Column(Float, nullable=True)
    ca_max = Column(Float, nullable=True)
    modele = Column(String, nullable=True)
    date_calcul = Column(Date, nullable=True)


class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    email = Column(String, nullable=False)
    login_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
