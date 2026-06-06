"""Tests for the /users endpoint."""


def test_create_user_success(client):
    r = client.post("/users", json={"email": "alice@example.com", "password": "secret"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "alice@example.com"
    assert "id" in body


def test_duplicate_email_returns_409(client):
    client.post("/users", json={"email": "bob@example.com", "password": "pass1"})
    r = client.post("/users", json={"email": "bob@example.com", "password": "pass2"})
    assert r.status_code == 409
    assert r.json()["detail"] == "Email already exists"
