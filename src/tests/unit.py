import pytest
from sqlmodel import SQLModel, Session, create_engine, select
from fastapi.testclient import TestClient

from main import app
from database import get_session
from models import UseCase
from utils import update_use_case, remove_dataset_from_use_case #get_use_case,


# ---------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------
@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh in-memory SQLite DB for each test."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Override DB dependency with the in-memory session."""
    def get_test_session():
        return session

    app.dependency_overrides[get_session] = get_test_session
    client = TestClient(app)

    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------
# TESTS
# ---------------------------------------------------------------------
def test_update_use_case_creates_record(session):
    """update_use_case() should create a new DB record when none exists."""
    update_use_case(
        session=session,
        use_case="aml1",
        node="NODE1",
        filename="file1.csv",
        num_records=10,
        num_features=3,
        schema=["a", "b", "c"]
    )

    result = session.exec(select(UseCase).where(UseCase.name == "aml1")).first()
    assert result is not None
    assert "NODE1" in result.datasets
    assert result.datasets["NODE1"] == ["file1.csv"]

    # Check metadata fields exist
    assert result.num_records == 10
    assert result.num_features == 3
    assert result.schema == ["a", "b", "c"]
    assert result.timestamp is not None


def test_update_use_case_appends_dataset(session):
    """Calling update twice should append dataset names under the same node."""
    # First insert
    update_use_case(
        session, "aml1", "NODE1", "file1.csv",
        num_records=10, num_features=3, schema=["a"]
    )

    # Append
    update_use_case(
        session, "aml1", "NODE1", "file2.csv",
        num_records=20, num_features=5, schema=["x", "y"]
    )

    result = session.exec(select(UseCase).where(UseCase.name == "aml1")).first()
    assert result.datasets["NODE1"] == ["file1.csv", "file2.csv"]

'''
def test_get_use_case(session):
    """Verify get_use_case returns correct use-case object."""
    update_use_case(
        session, "fraud", "NODE2", "abc.csv",
        num_records=7, num_features=2, schema=["col1", "col2"]
    )

    uc = get_use_case(session, "fraud")

    assert uc is not None
    assert "NODE2" in uc.datasets
    assert uc.num_records == 7
    assert uc.schema == ["col1", "col2"]
'''

def test_remove_dataset_from_use_case(session):
    """remove_dataset_from_use_case should remove file under node."""
    update_use_case(
        session, "aml1", "NODE1", "file1.csv",
        num_records=5, num_features=2, schema=["x"]
    )
    update_use_case(
        session, "aml1", "NODE1", "file2.csv",
        num_records=15, num_features=4, schema=["y"]
    )

    removed = remove_dataset_from_use_case(session, "aml1", "NODE1", "file1.csv")
    assert removed is True

    uc = get_use_case(session, "aml1")
    assert uc.datasets["NODE1"] == ["file2.csv"]


def test_remove_dataset_last_file_removes_node_key(session):
    """If the last file under a node is removed, the node key should disappear."""
    update_use_case(
        session, "aml1", "NODE1", "only.csv",
        num_records=1, num_features=1, schema=["c"]
    )

    remove_dataset_from_use_case(session, "aml1", "NODE1", "only.csv")

    uc = get_use_case(session, "aml1")
    assert "NODE1" not in uc.datasets
