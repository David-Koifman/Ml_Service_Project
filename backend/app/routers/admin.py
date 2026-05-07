from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_admin_user
from app.database import get_db
from app.models.promo import PromoCode
from app.models.user import User
from app.schemas.promo import PromoCodeCreate, PromoCodeOut

router = APIRouter()


@router.post("/promo", response_model=PromoCodeOut, status_code=201)
def create_promo(
    data: PromoCodeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    existing = db.query(PromoCode).filter(PromoCode.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Promo code already exists")

    promo = PromoCode(
        code=data.code.upper(),
        credits_amount=data.credits_amount,
        discount_percent=data.discount_percent,
        max_activations=data.max_activations,
        expires_at=data.expires_at,
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo


@router.get("/promo", response_model=list[PromoCodeOut])
def list_promos(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    return db.query(PromoCode).order_by(PromoCode.created_at.desc()).all()


@router.delete("/promo/{promo_id}", status_code=204)
def deactivate_promo(
    promo_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    promo = db.get(PromoCode, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    promo.is_active = False
    db.commit()
