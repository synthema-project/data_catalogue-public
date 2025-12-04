# tests/unit.py

import pytest
from sqlmodel import SQLModel, create_engine, Session

from utils import update_use_case
from models import UseCase


# -------------------------------------------------------
# FIX: Use in-memory SQLite DB to avoid real PostgreSQL
# -------------------------------------------------------
@pytest.fixture
def db():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# -------------------------------------------------------
# Unit Tests
# -------------------------------------------------------

def test_update_use_case_creates_record(db):
    update_use_case(db, "aml1", "NODE1", "file1.csv")

    record = db.get(UseCase, "aml1")
    assert record is not None
    assert "NODE1" in record.datasets
    assert record.datasets["NODE1"] == [
        "obstorageapi.k8s.synthema.rid-intrasoft.eu/file1.csv"
    ]


def test_update_use_case_appends(db):
    update_use_case(db, "aml1", "NODE1", "file1.csv")
    update_use_case(db, "aml1", "NODE1", "file2.csv")

    record = db.get(UseCase, "aml1")
    assert len(record.datasets["NODE1"]) == 2
    assert record.datasets["NODE1"][1].endswith("file2.csv")
