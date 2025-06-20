# database.py

import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.engine.url import make_url
import models  # Ensure this imports all your models

# Determine environment: 'prod' (default), 'integration', or 'unit'
ENV = os.getenv("ENV", "prod").lower()

# Database URL config
if ENV == "unit":
    DATABASE_URL = "sqlite:///:memory:"
elif ENV == "integration":
    DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///integration.db")
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")

# Create engine
# Create engine — allow thread access for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)


def get_engine():
    return engine

def get_db():
    """Yield a session bound to the configured engine."""
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    """Safely create tables — never in production without explicit override."""
    _ensure_not_production()
    SQLModel.metadata.create_all(engine)

def drop_all_tables():
    """Dangerous — only allowed in test environments."""
    _ensure_not_production()
    SQLModel.metadata.drop_all(engine)

def _ensure_not_production():
    """Prevent accidental schema changes to the real prod DB."""
    url = make_url(DATABASE_URL)
    if ENV == "prod":
        raise RuntimeError("❌ Cannot modify schema in production environment!")
    if "database.db" in url.database:
        raise RuntimeError("❌ Refusing to modify real production database.db!")
