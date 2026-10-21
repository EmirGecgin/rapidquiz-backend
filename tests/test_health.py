import pytest


@pytest.mark.django_db
def test_health_check_returns_ok(client):
    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_rejects_post(client):
    response = client.post("/api/v1/health/")

    assert response.status_code == 405
