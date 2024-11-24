import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from sqlmodel import create_engine, SQLModel, Session as TestSession
from models import NodeDatasetInfo

# Database setup for tests
DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def test_engine():
    """Create a test SQLite database engine."""
    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def test_session(test_engine):
    """Provide a database session for tests."""
    with TestSession(test_engine) as session:
        yield session

@pytest.fixture
async def test_client():
    """Provide an HTTP client for testing the FastAPI app."""
    from main import app  # Import the FastAPI app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_save_metadata(test_client, test_session):
    """Test saving metadata to the database."""
    payload = {
        "node": "test_node",
        "path": "/mock/path/test.csv",
        "disease": "test_disease"
    }

    response = await test_client.post("/metadata", json=payload)

    assert response.status_code == 200
    assert response.json() == {"message": "Metadata uploaded successfully"}

    # Verify the metadata is saved in the database
    statement = test_session.query(NodeDatasetInfo).filter_by(
        node="test_node", disease="test_disease", path="/mock/path/test.csv"
    ).first()
    assert statement is not None
    assert statement.node == "test_node"
    assert statement.disease == "test_disease"
    assert statement.path == "/mock/path/test.csv"

@pytest.mark.asyncio
async def test_retrieve_metadata(test_client, test_session):
    """Test retrieving metadata from the database."""
    # Prepopulate the database
    dataset = NodeDatasetInfo(node="test_node", path="/mock/path/test.csv", disease="test_disease")
    test_session.add(dataset)
    test_session.commit()

    response = await test_client.get("/metadata/test_disease", params={"node": "test_node"})

    assert response.status_code == 200
    assert response.json() == {
        "node": "test_node",
        "path": "/mock/path/test.csv",
        "disease": "test_disease",
    }

@pytest.mark.asyncio
async def test_delete_metadata(test_client, test_session):
    """Test deleting specific metadata."""
    # Prepopulate the database
    dataset = NodeDatasetInfo(node="test_node", path="/mock/path/test.csv", disease="test_disease")
    test_session.add(dataset)
    test_session.commit()

    response = await test_client.delete(
        "/metadata",
        params={"node": "test_node", "disease": "test_disease", "path": "/mock/path/test.csv"}
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Dataset '/mock/path/test.csv' deleted successfully."}

    # Verify the metadata is removed from the database
    statement = test_session.query(NodeDatasetInfo).filter_by(
        node="test_node", disease="test_disease", path="/mock/path/test.csv"
    ).first()
    assert statement is None

@pytest.mark.asyncio
async def test_delete_nonexistent_metadata(test_client):
    """Test deleting metadata that doesn't exist."""
    response = await test_client.delete(
        "/metadata",
        params={"node": "nonexistent_node", "disease": "nonexistent_disease", "path": "/mock/path/nonexistent.csv"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset '/mock/path/nonexistent.csv' not found."

@pytest.mark.asyncio
async def test_delete_all_metadata(test_client, test_session):
    """Test deleting all metadata from the database."""
    # Prepopulate the database
    dataset1 = NodeDatasetInfo(node="test_node_1", path="/mock/path/test1.csv", disease="disease_1")
    dataset2 = NodeDatasetInfo(node="test_node_2", path="/mock/path/test2.csv", disease="disease_2")
    test_session.add_all([dataset1, dataset2])
    test_session.commit()

    response = await test_client.delete("/metadata/all")

    assert response.status_code == 200
    assert response.json() == {"message": "All datasets deleted successfully."}

    # Verify the database is empty
    datasets = test_session.query(NodeDatasetInfo).all()
    assert len(datasets) == 0
