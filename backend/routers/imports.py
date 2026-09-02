from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

try:
    from backend.database import get_db
    from backend.import_service import DATASETS, validate_and_import
    from backend.routers.auth import require_roles
except ImportError:
    from database import get_db
    from import_service import DATASETS, validate_and_import
    from routers.auth import require_roles

router = APIRouter()


@router.post("/{dataset}")
async def import_dataset(
    dataset: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("admin")),
) -> dict:
    if dataset not in DATASETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de données non supporté. Choix possibles : {', '.join(DATASETS)}",
        )
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seuls les fichiers CSV sont acceptés")
    try:
        content = await file.read()
        return validate_and_import(db, dataset, content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Import annulé") from exc
