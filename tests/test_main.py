from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_renvoie_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_renvoie_la_variable_version(monkeypatch):
    monkeypatch.setenv("VERSION", "1.2.3")
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "1.2.3"}


def test_items_ok_quand_bug_rate_vaut_0(monkeypatch):
    monkeypatch.setenv("BUG_RATE", "0")
    response = client.get("/items")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_items_toujours_500_quand_bug_rate_vaut_1(monkeypatch):
    monkeypatch.setenv("BUG_RATE", "1")
    for _ in range(20):
        response = client.get("/items")
        assert response.status_code == 500
        assert response.json() == {"detail": "bug simulé"}
