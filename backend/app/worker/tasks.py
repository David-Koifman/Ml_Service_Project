import time
import joblib
import pandas as pd
from sqlalchemy.orm import Session

from app.worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.prediction import PredictionTask, TaskStatus
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.config import settings
from app.core.metrics import predictions_total, credits_spent_total, prediction_duration_seconds

NUMERIC_FEATURES = [
    "person_age", "person_income", "person_emp_exp",
    "loan_amnt", "loan_int_rate", "loan_percent_income",
    "cb_person_cred_hist_length", "credit_score",
]
CATEGORICAL_FEATURES = [
    "person_gender", "person_education",
    "person_home_ownership", "loan_intent",
    "previous_loan_defaults_on_file",
]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


@celery_app.task(name="run_prediction", bind=True)
def run_prediction(self, task_id: int, model_path: str, input_data: dict):
    db: Session = SessionLocal()
    task = db.get(PredictionTask, task_id)

    try:
        task.status = TaskStatus.running
        db.commit()

        start = time.time()
        pipeline = joblib.load(model_path)
        df = pd.DataFrame([input_data])[ALL_FEATURES]

        prediction = int(pipeline.predict(df)[0])
        probability = float(pipeline.predict_proba(df)[0][prediction])
        prediction_duration_seconds.observe(time.time() - start)

        result = {
            "approved": bool(prediction),
            "probability": round(probability, 4),
            "label": "Approved" if prediction == 1 else "Rejected",
        }

        # атомарно списываем кредиты и сохраняем результат
        user = db.get(User, task.user_id)
        cost = settings.PREDICTION_COST

        user.credits_balance -= cost
        task.result = result
        task.status = TaskStatus.done
        task.credits_cost = cost

        transaction = Transaction(
            user_id=task.user_id,
            amount=cost,
            type=TransactionType.debit,
            description=f"Prediction task #{task_id}",
            related_task_id=task_id,
        )
        db.add(transaction)
        db.commit()

        predictions_total.labels(status="done").inc()
        credits_spent_total.inc(cost)

    except Exception as exc:
        task.status = TaskStatus.failed
        task.result = {"error": str(exc)}
        db.commit()
        predictions_total.labels(status="failed").inc()
        raise self.retry(exc=exc, max_retries=0)
    finally:
        db.close()
