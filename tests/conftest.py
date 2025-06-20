# tests/conftest.py

import pytest
from sqlmodel import SQLModel, create_engine, Session
from main import app
from database import get_db
from fastapi.testclient import TestClient

# ✅ Create in-memory SQLite test engine
test_engine = create_engine("sqlite:///:memory:", echo=False)

# ✅ Session fixture initializes tables
@pytest.fixture()
def session_fixture():
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session

# ✅ Override FastAPI's get_db dependency
@pytest.fixture(autouse=True)
def override_get_db(session_fixture):
    def get_test_db():
        yield session_fixture
    app.dependency_overrides[get_db] = get_test_db
