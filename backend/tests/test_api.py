from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_health():
    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_documents_endpoint():
    response = client.get(
        "/api/v1/documents"
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "documents" in data


def test_invalid_document_type():
    response = client.post(
        "/api/v1/documents/process",
        data={
            "document_type": "unknown_type",
        },
    )

    assert response.status_code == 400