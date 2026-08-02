import pytest

from app import create_app, db
from models import Note, User


@pytest.fixture()
def client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def test_signup_login_check_session_and_crud(client):
    response = client.post(
        "/signup",
        json={"username": "alice", "password": "secret123"},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["username"] == "alice"
    assert "password" not in data

    response = client.post(
        "/login",
        json={"username": "alice", "password": "secret123"},
    )
    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"

    response = client.get("/me")
    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"

    response = client.post(
        "/notes",
        json={"title": "First note", "content": "Hello from the API", "category": "work"},
    )
    assert response.status_code == 201
    note_data = response.get_json()
    assert note_data["title"] == "First note"
    assert note_data["category"] == "work"

    response = client.get("/notes")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["items"][0]["title"] == "First note"
    assert payload["page"] == 1

    response = client.patch(
        f"/notes/{note_data['id']}",
        json={"content": "Updated content"},
    )
    assert response.status_code == 200
    assert response.get_json()["content"] == "Updated content"

    response = client.delete(f"/notes/{note_data['id']}")
    assert response.status_code == 204

    response = client.get("/notes")
    assert response.status_code == 200
    assert response.get_json()["items"] == []


def test_notes_are_isolated_between_users(client):
    client.post(
        "/signup",
        json={"username": "alice", "password": "secret123"},
    )
    client.post(
        "/login",
        json={"username": "alice", "password": "secret123"},
    )
    note_response = client.post(
        "/notes",
        json={"title": "Private note", "content": "Alice only", "category": "personal"},
    )
    note_id = note_response.get_json()["id"]

    client.post("/logout")

    client.post(
        "/signup",
        json={"username": "bob", "password": "secret123"},
    )
    client.post(
        "/login",
        json={"username": "bob", "password": "secret123"},
    )

    response = client.get(f"/notes/{note_id}")
    assert response.status_code == 404

    response = client.patch(f"/notes/{note_id}", json={"content": "Hacked"})
    assert response.status_code == 404

    response = client.delete(f"/notes/{note_id}")
    assert response.status_code == 404


def test_unauthenticated_requests_are_rejected(client):
    response = client.get("/notes")
    assert response.status_code == 401

    response = client.post(
        "/notes",
        json={"title": "No access", "content": "blocked", "category": "work"},
    )
    assert response.status_code == 401


def test_unknown_route_returns_404_not_401(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert response.get_json() == {"error": "not found"}

    client.post("/signup", json={"username": "alice", "password": "secret123"})

    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert response.get_json() == {"error": "not found"}


def test_missing_json_content_type_returns_json_error(client):
    response = client.post(
        "/signup",
        data="not json",
        content_type="text/plain",
    )
    assert response.status_code == 415
    assert response.content_type == "application/json"
    assert response.get_json() == {"error": "request must be JSON"}
