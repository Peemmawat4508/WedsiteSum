import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app, get_db
from database import Base

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

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_upload_document_txt(client):
    # Upload without auth
    files = {'file': ('test.txt', b'This is a test document content.', 'text/plain')}
    response = client.post(
        "/upload",
        files=files
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.txt"
    assert "id" in data
