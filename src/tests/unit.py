# tests/unit.py
import pytest
from sqlmodel import Session
from database import engine
from models import UseCase
from services.usecase_service import update_use_case


@pytest.fixture
def db():
    with Session(engine) as session:
        yield session


def test_update_use_case_creates_record(db):
    update_use_case(db, "aml1", "NODE1", "file1.csv")

    uc = db.get(UseCase, "aml1")
    assert uc is not None
    assert "NODE1" in uc.datasets
    assert uc.datasets["NODE1"] == ["obstorageapi.k8s.synthema.rid-intrasoft.eu/file1.csv"]


def test_update_use_case_appends_without_checks(db):
    update_use_case(db, "aml1", "NODE1", "file1.csv")
    update_use_case(db, "aml1", "NODE1", "file2.csv")
    update_use_case(db, "aml1", "NODE1", "file3.csv")

    uc = db.get(UseCase, "aml1")
    assert uc is not None
    assert len(uc.datasets["NODE1"]) == 3
