from datetime import datetime

from passlib.context import CryptContext

try:
    from backend.database import SessionLocal, ensure_schema
    from backend.models import Utilisateur
except ImportError:
    from database import SessionLocal, ensure_schema
    from models import Utilisateur


def create_admin_user(email: str = "admin@pme.cm", password: str = "Admin123!") -> None:
    ensure_schema()
    db = SessionLocal()
    try:
        user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
        if user:
            print(f"Utilisateur déjà présent : {email}")
            return

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user = Utilisateur(
            nom="Admin",
            email=email,
            mot_de_passe=pwd_context.hash(password),
            profil="admin",
            role="admin",
            boutique_id=None,
            is_active=True,
            date_creation=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        print(f"Utilisateur créé : {email} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
