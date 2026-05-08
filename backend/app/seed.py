import os

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.ml_model import MLModel
from app.models.user import User, UserRole

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
MODEL_PATH = "/app/ml_models/loan_model.joblib"


def seed():
    db = SessionLocal()
    try:
        # Создать админа если не существует
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                role=UserRole.admin,
                credits_balance=9999,
            )
            db.add(admin)
            db.flush()
            print(f"[seed] Admin created: {ADMIN_EMAIL}")
        else:
            print(f"[seed] Admin already exists: {ADMIN_EMAIL}")

        # Добавить модель в БД если не существует
        model = db.query(MLModel).filter(MLModel.file_path == MODEL_PATH).first()
        if not model and os.path.exists(MODEL_PATH):
            model = MLModel(
                user_id=admin.id,
                name="Кредитный скоринг v1",
                description="GradientBoostingClassifier, точность 93%",
                file_path=MODEL_PATH,
                is_active=True,
            )
            db.add(model)
            print("[seed] Model registered in DB")
        elif not os.path.exists(MODEL_PATH):
            print(f"[seed] Model file not found at {MODEL_PATH}, skipping")
        else:
            print("[seed] Model already in DB")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
