from datetime import datetime
from pydantic import BaseModel, Field

from app.models.transaction import TransactionType


class BalanceOut(BaseModel):
    credits_balance: int

    model_config = {"from_attributes": True}


class TopUpRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Amount of credits to add")
    payment_method: str = Field(default="card", description="Payment method (mock)")


class TopUpOut(BaseModel):
    success: bool
    credits_added: int
    bonus: int
    discount: int
    new_balance: int


class TransactionOut(BaseModel):
    id: int
    amount: int
    type: TransactionType
    description: str | None
    related_task_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
