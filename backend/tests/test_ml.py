import io
import joblib
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression


VALID_INPUT = {
    "person_age": 25.0,
    "person_gender": "male",
    "person_education": "Bachelor",
    "person_income": 50000.0,
    "person_emp_exp": 2.0,
    "person_home_ownership": "RENT",
    "loan_amnt": 10000.0,
    "loan_intent": "PERSONAL",
    "loan_int_rate": 12.5,
    "loan_percent_income": 0.2,
    "cb_person_cred_hist_length": 3.0,
    "credit_score": 650,
    "previous_loan_defaults_on_file": "No",
}


def make_test_model():
    X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
    y = np.array([0, 1, 0, 1])
    pipeline = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression())])
    pipeline.fit(X, y)
    return pipeline


def upload_model(client, admin_headers):
    model_bytes = io.BytesIO()
    joblib.dump(make_test_model(), model_bytes)
    model_bytes.seek(0)

    resp = client.post(
        "/models/upload",
        data={"name": "Test Model", "description": "Test"},
        files={"file": ("test_model.joblib", model_bytes, "application/octet-stream")},
        headers=admin_headers,
    )
    return resp


def test_upload_model(client, admin_headers):
    resp = upload_model(client, admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Model"
    assert data["is_active"] is True


def test_upload_wrong_extension(client, admin_headers):
    resp = client.post(
        "/models/upload",
        data={"name": "Bad"},
        files={"file": ("model.pkl", b"data", "application/octet-stream")},
        headers=admin_headers,
    )
    assert resp.status_code == 400
    assert ".joblib" in resp.json()["detail"]


def test_list_models(client, admin_headers, auth_headers):
    upload_model(client, admin_headers)
    upload_model(client, admin_headers)
    resp = client.get("/models/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_delete_model(client, admin_headers, auth_headers):
    model_id = upload_model(client, admin_headers).json()["id"]
    resp = client.delete(f"/models/{model_id}", headers=admin_headers)
    assert resp.status_code == 204

    resp = client.get("/models/", headers=auth_headers)
    assert len(resp.json()) == 0


def test_create_prediction_insufficient_credits(client, admin_headers, auth_headers, db):
    from app.models.user import User
    user = db.query(User).filter(User.email == "test@example.com").first()
    user.credits_balance = 0
    db.commit()

    model_id = upload_model(client, admin_headers).json()["id"]
    resp = client.post(
        f"/predictions/?model_id={model_id}",
        json=VALID_INPUT,
        headers=auth_headers,
    )
    assert resp.status_code == 402
    assert "Insufficient credits" in resp.json()["detail"]


def test_create_prediction_task_created(client, admin_headers, auth_headers):
    model_id = upload_model(client, admin_headers).json()["id"]

    with patch("app.routers.predictions.run_prediction") as mock_task:
        mock_task.delay.return_value = MagicMock(id="celery-task-123")
        resp = client.post(
            f"/predictions/?model_id={model_id}",
            json=VALID_INPUT,
            headers=auth_headers,
        )

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"
    assert data["model_id"] == model_id


def test_get_prediction_not_found(client, auth_headers):
    resp = client.get("/predictions/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_list_predictions(client, auth_headers):
    resp = client.get("/predictions/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
