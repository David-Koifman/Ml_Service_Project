import os
import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_admin_user, get_current_user
from app.database import get_db
from app.models.ml_model import MLModel
from app.models.user import User
from app.schemas.ml_model import MLModelOut

router = APIRouter()


@router.post("/upload", response_model=MLModelOut, status_code=201)
def upload_model(
    name: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    if not file.filename.endswith(".joblib"):
        raise HTTPException(status_code=400, detail="Only .joblib files are allowed")

    os.makedirs(settings.MODEL_STORAGE, exist_ok=True)
    file_path = os.path.join(settings.MODEL_STORAGE, f"user_{current_user.id}_{file.filename}")

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    model = MLModel(
        user_id=current_user.id,
        name=name,
        description=description,
        file_path=file_path,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/", response_model=list[MLModelOut])
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(MLModel).filter(MLModel.is_active == True).all()


@router.delete("/{model_id}", status_code=204)
def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    model = db.get(MLModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    model.is_active = False
    db.commit()
