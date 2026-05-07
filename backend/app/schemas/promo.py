from datetime import datetime
from pydantic import BaseModel, Field


class PromoCodeCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    credits_amount: int = Field(default=0, ge=0)
    discount_percent: int = Field(default=0, ge=0, le=100)
    max_activations: int | None = Field(default=None, gt=0)
    expires_at: datetime | None = None


class PromoCodeOut(BaseModel):
    id: int
    code: str
    credits_amount: int
    discount_percent: int
    max_activations: int | None
    current_activations: int
    expires_at: datetime | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PromoActivateRequest(BaseModel):
    code: str


class PromoActivateOut(BaseModel):
    success: bool
    credits_added: int
    new_balance: int
    message: str
