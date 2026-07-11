from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Client, SegmentRFM
from backend.routers.auth import get_current_user

router = APIRouter()


@router.get("/segments")
def get_segments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list:
    segments = (
        db.query(
            SegmentRFM.segment,
            func.count(SegmentRFM.id_client).label("nb_clients"),
            func.avg(SegmentRFM.recence).label("recence_moyenne"),
            func.avg(SegmentRFM.frequence).label("frequence_moyenne"),
            func.avg(SegmentRFM.montant).label("montant_moyen"),
        )
        .group_by(SegmentRFM.segment)
        .all()
    )

    result = [
        {
            "segment": seg[0],
            "nb_clients": seg[1],
            "recence_moyenne": round(seg[2], 2) if seg[2] else 0,
            "frequence_moyenne": round(seg[3], 2) if seg[3] else 0,
            "montant_moyen": round(seg[4], 2) if seg[4] else 0,
        }
        for seg in segments
    ]
    return result


@router.get("/clients")
def get_clients(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list:
    clients = (
        db.query(
            Client.id_client,
            Client.nom,
            Client.prenom,
            Client.telephone,
            Client.region,
            SegmentRFM.segment,
            SegmentRFM.recence,
            SegmentRFM.frequence,
            SegmentRFM.montant,
        )
        .outerjoin(SegmentRFM, Client.id_client == SegmentRFM.id_client)
        .all()
    )

    result = [
        {
            "id_client": client[0],
            "nom": client[1],
            "prenom": client[2],
            "telephone": client[3],
            "region": client[4],
            "segment": client[5],
            "recence": client[6],
            "frequence": client[7],
            "montant": client[8],
        }
        for client in clients
    ]
    return result
