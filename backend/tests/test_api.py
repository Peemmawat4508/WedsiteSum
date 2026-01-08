import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app, get_db
from database import Base
from models import User

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    # Create tables
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    # Drop tables (optional for in-memory)
    Base.metadata.drop_all(bind=engine)

def test_register_user(client):
    response = client.post(
        "/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_register_existing_user(client):
    response = client.post(
        "/register",
        json={"email": "test@example.com", "password": "param", "full_name": "Test User"}
    )
    assert response.status_code == 400

def test_login_user(client):
    response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]

def test_read_users_me(client):
    # Login first
    login_response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"

def test_upload_document_txt(client):
    # Login
    login_response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Upload
    files = {'file': ('test.txt', b'This is a test document content.', 'text/plain')}
    response = client.post(
        "/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.txt"
    assert "id" in data
