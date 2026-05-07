import pytest


def test_register_success(client):
    resp = client.post("/auth/register", json={"email": "user@test.com", "password": "pass123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "user@test.com"
    assert data["role"] == "user"
    assert data["credits_balance"] == 100


def test_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "dup@test.com", "password": "pass123"})
    resp = client.post("/auth/register", json={"email": "dup@test.com", "password": "pass123"})
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_register_invalid_email(client):
    resp = client.post("/auth/register", json={"email": "not-an-email", "password": "pass123"})
    assert resp.status_code == 422


def test_login_success(client, registered_user):
    resp = client.post("/auth/login", data={"username": "test@example.com", "password": "password123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, registered_user):
    resp = client.post("/auth/login", data={"username": "test@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/auth/login", data={"username": "nobody@test.com", "password": "pass"})
    assert resp.status_code == 401


def test_get_me(client, auth_headers):
    resp = client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["credits_balance"] == 100


def test_get_me_no_token(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_get_me_invalid_token(client):
    resp = client.get("/users/me", headers={"Authorization": "Bearer bad.token.here"})
    assert resp.status_code == 401
