# tests/conftest.py

import os
import pytest
from sqlmodel import SQLModel, Session
from main import app
from database import get_db, drop_all_tables, create_db_and_tables, get_engine

# 🚨 Force test mode
os.environ["ENV"] = "unit"

# ✅ Use engine from database.py (will respect ENV)
engine = get_engine()

# ✅ Setup and teardown test database schema
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    drop_all_tables()
    create_db_and_tables()

# ✅ Yield test session from engine
@pytest.fixture()
def session_fixture():
    with Session(engine) as session:
        yield session

# ✅ Override app DB dependency
@pytest.fixture(autouse=True)
def override_get_db(session_fixture):
    def get_test_db():
        yield session_fixture
    app.dependency_overrides[get_db] = get_test_db
