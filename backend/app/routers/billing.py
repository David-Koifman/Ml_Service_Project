from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.billing import BalanceOut, TopUpRequest, TopUpOut, TransactionOut
from app.services.billing import get_balance, get_transactions, topup_balance

router = APIRouter()


@router.get("/balance", response_model=BalanceOut)
def balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"credits_balance": get_balance(current_user.id, db)}


@router.post("/topup", response_model=TopUpOut)
def topup(
    data: TopUpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Пополнение баланса через платёжный шлюз (mock).
    Если у пользователя есть активная скидка от промокода — она применяется автоматически.
    """
    result = topup_balance(current_user.id, data.amount, db)
    return TopUpOut(success=True, **result)


@router.get("/transactions", response_model=list[TransactionOut])
def transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_transactions(current_user.id, db)
