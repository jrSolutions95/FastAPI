# database.py

from sqlmodel import SQLModel, create_engine, Session
import models

sqllite_filename = "database.db"
sqllite_url = f"sqlite:///{sqllite_filename}"

engine = create_engine(sqllite_url, echo=True)

def get_engine():
    return engine

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

    # database.py
def get_db():
    with Session(engine) as session:
        yield session

