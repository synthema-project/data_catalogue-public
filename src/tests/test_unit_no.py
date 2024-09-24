import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from main import app
from models import NodeDatasetInfo, RemoveDatasetObject
from utils import save_dataset_info_to_database, get_dataset_info_from_database, remove_dataset_info_from_database, fetch_all_datasets, remove_all_datasets_from_database
from database import get_session

# Create a TestClient for FastAPI app
client = TestClient(app)

# Mock the database session dependency
@pytest.fixture
def mock_session():
    session = MagicMock(spec=Session)
    return session

# Override the dependency with mock session in FastAPI
app.dependency_overrides[get_session] = lambda: mock_session()

# Sample data for testing
node_dataset = NodeDatasetInfo(id=1, node="Node1", path="/path/to/data", disease="Disease1")
remove_dataset = RemoveDatasetObject(node="Node1", disease="Disease1", path="/path/to/data")


# Test saving dataset info
def test_save_dataset_info(mock_session):
    mock_session.commit.return_value = None  # Mock commit
    response = client.post("/metadata", json=node_dataset.dict())
    assert response.status_code == 200
    assert response.json() == {"message": "Metadata uploaded successfully"}


# Test retrieving dataset info
def test_retrieve_dataset_info(mock_session):
    mock_session.exec.return_value.first.return_value = node_dataset
    response = client.get(f"/metadata/{node_dataset.disease}?node={node_dataset.node}")
    assert response.status_code == 200
    assert response.json() == node_dataset.dict()


# Test retrieving all datasets
@pytest.mark.asyncio
async def test_get_all_datasets(mock_session):
    mock_session.exec.return_value.all.return_value = [node_dataset]
    response = client.get("/metadata")
    assert response.status_code == 200
    assert response.json() == {"datasets": [node_dataset.dict()]}


# Test deleting a specific dataset
def test_delete_dataset(mock_session):
    mock_session.exec.return_value.first.return_value = node_dataset
    response = client.delete("/metadata", json=remove_dataset.dict())
    assert response.status_code == 200
    assert response.json() == {"message": f"Dataset '{remove_dataset.path}' deleted successfully."}


# Test deleting all datasets
def test_delete_all_datasets(mock_session):
    mock_session.exec.return_value.all.return_value = [node_dataset]
    response = client.delete("/metadata/all")
    assert response.status_code == 200
    assert response.json() == {"message": "All datasets deleted successfully."}


# Test healthcheck endpoint
def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
