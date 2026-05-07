from datetime import datetime, timedelta, timezone


def create_promo(client, admin_headers, **kwargs):
    data = {"code": "TEST100", "credits_amount": 100, **kwargs}
    return client.post("/admin/promo", json=data, headers=admin_headers)


def test_admin_create_promo(client, admin_headers):
    resp = create_promo(client, admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "TEST100"
    assert data["credits_amount"] == 100
    assert data["is_active"] is True


def test_admin_create_promo_duplicate(client, admin_headers):
    create_promo(client, admin_headers)
    resp = create_promo(client, admin_headers)
    assert resp.status_code == 400


def test_admin_only(client, auth_headers):
    resp = client.post("/admin/promo", json={"code": "X", "credits_amount": 10}, headers=auth_headers)
    assert resp.status_code == 403


def test_activate_promo(client, auth_headers, admin_headers):
    create_promo(client, admin_headers, code="GIFT50", credits_amount=50)

    resp = client.post("/promo/activate", json={"code": "GIFT50"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["credits_added"] == 50
    assert data["new_balance"] == 150


def test_activate_promo_twice(client, auth_headers, admin_headers):
    create_promo(client, admin_headers, code="ONCE", credits_amount=50)
    client.post("/promo/activate", json={"code": "ONCE"}, headers=auth_headers)

    resp = client.post("/promo/activate", json={"code": "ONCE"}, headers=auth_headers)
    assert resp.status_code == 400
    assert "already activated" in resp.json()["detail"]


def test_activate_nonexistent_promo(client, auth_headers):
    resp = client.post("/promo/activate", json={"code": "FAKE999"}, headers=auth_headers)
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"]


def test_activate_expired_promo(client, auth_headers, admin_headers):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    create_promo(client, admin_headers, code="EXPIRED", credits_amount=50, expires_at=past)

    resp = client.post("/promo/activate", json={"code": "EXPIRED"}, headers=auth_headers)
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"]


def test_activate_promo_limit_reached(client, admin_headers, db):
    from app.core.security import hash_password
    from app.models.user import User

    create_promo(client, admin_headers, code="LIMITED", credits_amount=10, max_activations=1)

    user2 = User(email="user2@test.com", password_hash=hash_password("pass123"))
    db.add(user2)
    db.commit()

    client.post("/auth/login", data={"username": "admin@example.com", "password": "admin123"})
    client.post("/promo/activate", json={"code": "LIMITED"}, headers=admin_headers)

    resp2 = client.post("/auth/login", data={"username": "user2@test.com", "password": "pass123"})
    headers2 = {"Authorization": f"Bearer {resp2.json()['access_token']}"}
    resp = client.post("/promo/activate", json={"code": "LIMITED"}, headers=headers2)
    assert resp.status_code == 400
    assert "limit reached" in resp.json()["detail"]


def test_promo_case_insensitive(client, auth_headers, admin_headers):
    create_promo(client, admin_headers, code="UPPER", credits_amount=25)
    resp = client.post("/promo/activate", json={"code": "upper"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["credits_added"] == 25
