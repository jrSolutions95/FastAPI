from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    print("Response text:", response.text)  # Debug output
    assert response.status_code == 200
    assert "<h1>Home page</h1>" in response.text
    assert "http://127.0.0.1:8000/docs" in response.text