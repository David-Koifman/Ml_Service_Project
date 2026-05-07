from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.core.metrics import credits_added_total


def get_balance(user_id: int, db: Session) -> int:
    user = db.get(User, user_id)
    return user.credits_balance


def topup_balance(user_id: int, amount: int, db: Session) -> dict:
    """Пополнение баланса — атомарная операция с SELECT FOR UPDATE.
    Если у пользователя есть скидка от промокода — применяется и сбрасывается.
    """
    user = db.execute(
        select(User).where(User.id == user_id).with_for_update()
    ).scalar_one()

    discount = user.topup_discount_percent
    bonus = int(amount * discount / 100)
    total = amount + bonus

    user.credits_balance += total
    user.topup_discount_percent = 0  # сбрасываем скидку после применения

    description = "Balance top-up via payment gateway"
    if discount > 0:
        description += f" (+{discount}% promo discount, +{bonus} bonus credits)"

    transaction = Transaction(
        user_id=user_id,
        amount=total,
        type=TransactionType.credit,
        description=description,
    )
    db.add(transaction)
    db.commit()
    db.refresh(user)
    credits_added_total.labels(source="topup").inc(total)
    return {"new_balance": user.credits_balance, "credits_added": total, "bonus": bonus, "discount": discount}


def get_transactions(user_id: int, db: Session, limit: int = 50) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )
