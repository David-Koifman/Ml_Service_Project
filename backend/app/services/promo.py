from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.promo import PromoActivation, PromoCode
from app.models.transaction import Transaction, TransactionType
from app.models.user import User


class PromoError(Exception):
    pass


def activate_promo(user_id: int, code: str, db: Session) -> dict:
    # блокируем строку промокода для атомарности
    promo = db.execute(
        select(PromoCode).where(PromoCode.code == code).with_for_update()
    ).scalar_one_or_none()

    if not promo:
        raise PromoError("Promo code not found")

    if not promo.is_active:
        raise PromoError("Promo code is inactive")

    # проверка срока действия (совместимо с SQLite naive datetime)
    if promo.expires_at:
        expires = promo.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            raise PromoError("Promo code has expired")

    # проверка лимита активаций
    if promo.max_activations is not None and promo.current_activations >= promo.max_activations:
        raise PromoError("Promo code activation limit reached")

    # проверка что пользователь ещё не активировал этот промокод
    already_used = db.execute(
        select(PromoActivation).where(
            PromoActivation.promo_code_id == promo.id,
            PromoActivation.user_id == user_id,
        )
    ).scalar_one_or_none()

    if already_used:
        raise PromoError("You have already activated this promo code")

    # всё ок — начисляем кредиты и/или сохраняем скидку
    user = db.execute(
        select(User).where(User.id == user_id).with_for_update()
    ).scalar_one()

    credits_added = promo.credits_amount
    user.credits_balance += credits_added
    promo.current_activations += 1

    # сохраняем скидку на следующее пополнение (берём максимальную из существующей)
    if promo.discount_percent > 0:
        user.topup_discount_percent = max(user.topup_discount_percent, promo.discount_percent)

    activation = PromoActivation(promo_code_id=promo.id, user_id=user_id)
    db.add(activation)

    if credits_added > 0:
        transaction = Transaction(
            user_id=user_id,
            amount=credits_added,
            type=TransactionType.credit,
            description=f"Promo code activation: {code}",
        )
        db.add(transaction)

    db.commit()
    db.refresh(user)

    msg = f"Promo code activated!"
    if credits_added > 0:
        msg += f" +{credits_added} credits"
    if promo.discount_percent > 0:
        msg += f" +{promo.discount_percent}% discount on next top-up"

    return {
        "success": True,
        "credits_added": credits_added,
        "new_balance": user.credits_balance,
        "message": msg,
    }
