import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from backend.database import get_db
    from backend.models import Boutique, LoginHistory, Utilisateur
except ImportError:
    from database import get_db
    from models import Boutique, LoginHistory, Utilisateur

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def _get_secret_key() -> str:
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY doit être défini dans les variables d'environnement")
    return SECRET_KEY


class LoginRequest(BaseModel):
    email: str
    mot_de_passe: str


class CreateUserRequest(BaseModel):
    nom: str
    email: str
    mot_de_passe: str
    profil: str = "analyste"
    role: str = "analyst"
    boutique_id: Optional[str] = None
    is_active: bool = True


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    boutique_id: Optional[str] = None
    is_active: Optional[bool] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    nom: str
    email: str
    profil: str
    role: str
    boutique_id: Optional[str] = None
    is_active: bool


class LoginHistoryResponse(BaseModel):
    id: int
    user_id: int
    email: str
    login_time: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(Utilisateur).filter(Utilisateur.email == payload.email).first()
    if not user or not pwd_context.verify(payload.mot_de_passe, user.mot_de_passe):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if not getattr(user, "is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Utilisateur désactivé")

    access_token = create_access_token(
        {
            "sub": user.email,
            "user_id": user.id,
            "profil": user.profil,
            "role": user.role,
            "boutique_id": user.boutique_id,
        },
        expires_delta=timedelta(minutes=60),
    )

    history = LoginHistory(
        user_id=user.id,
        email=user.email,
        login_time=datetime.utcnow(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(history)
    db.commit()

    return TokenResponse(access_token=access_token, token_type="bearer")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token invalide")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token invalide") from exc

    user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user


def require_roles(*allowed_roles):
    def _dependency(current_user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Droits insuffisants")
        return current_user

    return _dependency


@router.post("/users", response_model=UserResponse)
def create_user(
    payload: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
) -> UserResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul un administrateur peut créer un utilisateur")

    if db.query(Utilisateur).filter(Utilisateur.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cet email est déjà utilisé")

    if payload.role not in {"admin", "analyst", "manager", "boutique"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rôle invalide")

    if payload.role == "boutique" and not payload.boutique_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Boutique requise pour le rôle boutique",
        )

    user = Utilisateur(
        nom=payload.nom,
        email=payload.email,
        mot_de_passe=pwd_context.hash(payload.mot_de_passe),
        profil=payload.profil,
        role=payload.role,
        boutique_id=payload.boutique_id,
        is_active=payload.is_active,
        date_creation=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        nom=user.nom,
        email=user.email,
        profil=user.profil,
        role=user.role,
        boutique_id=user.boutique_id,
        is_active=user.is_active,
    )


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
) -> list[UserResponse]:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul un administrateur peut lister les utilisateurs")

    users = db.query(Utilisateur).order_by(Utilisateur.nom).all()
    return [
        UserResponse(
            id=u.id,
            nom=u.nom,
            email=u.email,
            profil=u.profil,
            role=u.role or "inconnu",
            boutique_id=u.boutique_id,
            is_active=u.is_active,
        )
        for u in users
    ]


@router.get("/boutiques")
def list_boutiques(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
) -> list[dict]:
    boutiques = db.query(Boutique).order_by(Boutique.id_boutique).all()
    return [
        {"id_boutique": b.id_boutique, "nom_boutique": b.nom_boutique}
        for b in boutiques
    ]


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
) -> Response:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul un administrateur peut supprimer un utilisateur")

    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vous ne pouvez pas supprimer votre propre compte")

    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/login-history", response_model=list[LoginHistoryResponse])
def login_history(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
) -> list[LoginHistoryResponse]:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul un administrateur peut consulter l'historique des connexions")

    history = db.query(LoginHistory).order_by(LoginHistory.login_time.desc()).limit(100).all()
    return [
        LoginHistoryResponse(
            id=h.id,
            user_id=h.user_id,
            email=h.email,
            login_time=h.login_time,
            ip_address=h.ip_address,
            user_agent=h.user_agent,
        )
        for h in history
    ]


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
) -> UserResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul un administrateur peut modifier un utilisateur")

    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    if payload.role:
        if payload.role not in {"admin", "analyst", "manager", "boutique"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rôle invalide")
        if payload.role == "boutique" and not (payload.boutique_id or user.boutique_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Boutique requise pour le rôle boutique",
            )
        user.role = payload.role

    if payload.boutique_id is not None:
        user.boutique_id = payload.boutique_id

    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        nom=user.nom,
        email=user.email,
        profil=user.profil,
        role=user.role,
        boutique_id=user.boutique_id,
        is_active=user.is_active,
    )


@router.get("/me")
def get_me(current_user: Utilisateur = Depends(get_current_user)) -> dict:
    return {
        "id": current_user.id,
        "nom": current_user.nom,
        "email": current_user.email,
        "profil": current_user.profil,
        "role": current_user.role,
        "boutique_id": current_user.boutique_id,
        "is_active": current_user.is_active,
    }
