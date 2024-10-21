import json
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
from main import app
from database import get_session
from models import NodeDatasetInfo

# Set up an SQLite in-memory database for testing
TEST_DATABASE_URL = "sqlite:///./test.db"  # SQLite database for testing
engine = create_engine(TEST_DATABASE_URL, echo=True)

# Path for example data (assuming some example data for testing if needed)
current_dir = Path(__file__).resolve().parent
example_data_dir = current_dir / "Example_data"

# Override session dependency to use SQLite instead of the main database
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

# Create database and tables for the test
def create_test_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Test client for FastAPI
client = TestClient(app)

# Base URL for the API
BASE_URL = "http://data-catalogue.k8s.synthema.rid-intrasoft.eu:83"

# Test healthcheck endpoint
def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Test creating a dataset
def test_save_dataset_info():
    create_test_db_and_tables()  # Ensure database is set up before running the test

    dataset_info = {
        "node": "node1",
        "path": "/path/to/data",
        "disease": "disease1"
    }

    response = client.post(f"{BASE_URL}/metadata", json=dataset_info)
    assert response.status_code == 200, f"Expected 200 OK but got {response.status_code}"
    assert response.json() == {"message": "Metadata uploaded successfully"}

# Test retrieving dataset info by node and disease
def test_get_dataset_info():
    response = client.get(f"{BASE_URL}/metadata?node=node1&disease=disease1")
    assert response.status_code == 200
    data = response.json()
    #assert 'node' in data['datasets'][0], f"Response JSON does not contain 'node' key: {data}"
    assert data['datasets'][0]["node"] == "node1"
    assert data['datasets'][0]["disease"] == "disease1"
    assert data['datasets'][0]["path"] == "/path/to/data"

# Test retrieving all datasets
def test_get_all_datasets():
    response = client.get(f"{BASE_URL}/metadata")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["datasets"], list)
    assert len(data["datasets"]) > 0  # Ensure there's at least one dataset

# Test deleting a specific dataset
def test_delete_dataset():
    dataset_info = {
        "node": "node1",
        "disease": "disease1",
        "path": "/path/to/data"
    }

    response = client.delete(f"{BASE_URL}/metadata", json=dataset_info)
    assert response.status_code == 200, f"Expected 200 OK but got {response.status_code}"
    assert response.json() == {"message": f"Dataset '{dataset_info['path']}' deleted successfully."}

# Test deleting all datasets
def test_delete_all_datasets():
    response = client.delete(f"{BASE_URL}/metadata/all")
    assert response.status_code == 200, f"Expected 200 OK but got {response.status_code}"
    assert response.json() == {"message": "All datasets deleted successfully."}

# Run tests sequentially
if __name__ == "__main__":
    test_healthcheck()
    test_save_dataset_info()
    test_get_dataset_info()
    test_get_all_datasets()
    test_delete_dataset()
    test_delete_all_datasets()
