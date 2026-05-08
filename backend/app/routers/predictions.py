from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.ml_model import MLModel
from app.models.prediction import PredictionTask
from app.models.user import User
from app.schemas.ml_model import PredictionRequest, PredictionTaskOut
from app.worker.tasks import run_prediction
from app.config import settings

router = APIRouter()


@router.post(
    "/",
    response_model=PredictionTaskOut,
    status_code=202,
    summary="Создать задачу предсказания",
    description="""
Отправляет данные заёмщика на ML-модель. Обработка **асинхронная** (Celery).

- Возвращает задачу со статусом `pending`
- Стоимость: **10 кредитов** (списываются только при успешном выполнении)
- Проверяйте результат через `GET /predictions/{id}`
    """,
)
def create_prediction(
    model_id: int,
    data: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.credits_balance < settings.PREDICTION_COST:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    model = db.get(MLModel, model_id)
    if not model or not model.is_active:
        raise HTTPException(status_code=404, detail="Model not found")

    task = PredictionTask(
        user_id=current_user.id,
        model_id=model_id,
        input_data=data.model_dump(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    celery_task = run_prediction.delay(task.id, model.file_path, data.model_dump())
    task.celery_task_id = celery_task.id
    db.commit()

    return task


@router.get("/", response_model=list[PredictionTaskOut], summary="История предсказаний", description="Последние 50 запросов текущего пользователя.")
def list_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(PredictionTask).filter(
        PredictionTask.user_id == current_user.id
    ).order_by(PredictionTask.created_at.desc()).limit(50).all()


@router.get("/{task_id}", response_model=PredictionTaskOut, summary="Статус и результат предсказания", description="Статусы: `pending` → `running` → `done` / `failed`. Результат доступен при статусе `done`.")
def get_prediction(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.get(PredictionTask, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
