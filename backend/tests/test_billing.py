def test_get_balance(client, auth_headers):
    resp = client.get("/billing/balance", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["credits_balance"] == 100


def test_topup_balance(client, auth_headers):
    resp = client.post("/billing/topup", json={"amount": 200}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["credits_added"] == 200
    assert data["new_balance"] == 300


def test_topup_invalid_amount(client, auth_headers):
    resp = client.post("/billing/topup", json={"amount": 0}, headers=auth_headers)
    assert resp.status_code == 422


def test_topup_negative_amount(client, auth_headers):
    resp = client.post("/billing/topup", json={"amount": -50}, headers=auth_headers)
    assert resp.status_code == 422


def test_transactions_history(client, auth_headers):
    client.post("/billing/topup", json={"amount": 100}, headers=auth_headers)
    client.post("/billing/topup", json={"amount": 50}, headers=auth_headers)

    resp = client.get("/billing/transactions", headers=auth_headers)
    assert resp.status_code == 200
    transactions = resp.json()
    assert len(transactions) == 2
    amounts = {t["amount"] for t in transactions}
    assert amounts == {100, 50}
    assert all(t["type"] == "credit" for t in transactions)


def test_topup_with_promo_discount(client, auth_headers, admin_headers):
    # создаём промокод со скидкой 20%
    client.post("/admin/promo", json={"code": "DISC20", "credits_amount": 0, "discount_percent": 20}, headers=admin_headers)
    client.post("/promo/activate", json={"code": "DISC20"}, headers=auth_headers)

    # пополняем на 100 кредитов — должны получить 120 (100 + 20% бонус)
    resp = client.post("/billing/topup", json={"amount": 100}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["credits_added"] == 120
    assert data["bonus"] == 20
    assert data["discount"] == 20
    assert data["new_balance"] == 220  # 100 начальных + 120

    # скидка должна сброситься после применения
    resp2 = client.post("/billing/topup", json={"amount": 100}, headers=auth_headers)
    assert resp2.json()["credits_added"] == 100
    assert resp2.json()["bonus"] == 0


def test_balance_no_auth(client):
    resp = client.get("/billing/balance")
    assert resp.status_code == 401
