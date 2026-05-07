from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.promo import PromoActivateOut, PromoActivateRequest
from app.services.promo import PromoError, activate_promo

router = APIRouter()


@router.post("/activate", response_model=PromoActivateOut)
def activate(
    data: PromoActivateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = activate_promo(current_user.id, data.code.upper(), db)
        return result
    except PromoError as e:
        raise HTTPException(status_code=400, detail=str(e))
