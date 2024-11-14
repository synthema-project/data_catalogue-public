import pytest
from sqlmodel import Session, SQLModel, create_engine
from fastapi.testclient import TestClient
from main import app
from database import get_session
from models import NodeDatasetInfo
from utils import save_dataset_info_to_database, get_dataset_info_from_database, remove_dataset_info_from_database

# Create a new in-memory SQLite engine for testing
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")  # In-memory SQLite
    SQLModel.metadata.create_all(engine)  # Create tables
    with Session(engine) as session:
        yield session

# Override the dependency to use the mock session
@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_test_session():
        return session

    app.dependency_overrides[get_session] = get_test_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_save_dataset_info_to_database(session):
    # Create a NodeDatasetInfo object
    dataset = NodeDatasetInfo(node="node1", path="/path/to/data", disease="disease1")
    
    # Test saving dataset info
    save_dataset_info_to_database(session, dataset)
    
    # Verify that it was saved correctly
    result = session.query(NodeDatasetInfo).filter_by(node="node1", disease="disease1").first()
    assert result is not None
    assert result.node == "node1"

def test_get_dataset_info_from_database(session):
    # Add a dataset for testing
    dataset = NodeDatasetInfo(node="node1", path="/path/to/data", disease="disease1")
    session.add(dataset)
    session.commit()

    # Test retrieving dataset info
    result = get_dataset_info_from_database(session, "node1", "disease1")
    
    # Verify the result
    assert result.node == "node1"
    assert result.disease == "disease1"

def test_remove_dataset_info_from_database(session):
    # Add a dataset for testing
    dataset = NodeDatasetInfo(node="node1", path="/path/to/data", disease="disease1")
    session.add(dataset)
    session.commit()

    # Test removing the dataset
    removed = remove_dataset_info_from_database(session, "node1", "disease1", "/path/to/data")
    
    # Verify it was removed
    assert removed is True
    assert session.query(NodeDatasetInfo).filter_by(node="node1", disease="disease1").first() is None
