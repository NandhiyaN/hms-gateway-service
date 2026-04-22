from fastapi.testclient import TestClient
from gateway import app

client = TestClient(app)


def test_health():
    # Verifies gateway health endpoint.
    response = client.get("/health")
    assert response.status_code == 200


def test_login_success():
    # Verifies successful login returns a mock bearer token.
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "admin_pass"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_login_failure():
    # Verifies invalid credentials are rejected.
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "wrong"}
    )
    assert response.status_code == 401


def test_me():
    # Verifies auth/me reads role from bearer token.
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer admin_test"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"