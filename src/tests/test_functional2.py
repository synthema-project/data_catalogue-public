import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
from main import app
from database import get_session
from models import NodeDatasetInfo

# Set up an SQLite in-memory database for testing
TEST_DATABASE_URL = "sqlite:///./test.db"  # Use SQLite for testing
engine = create_engine(TEST_DATABASE_URL, echo=True)

# Create a new SQLite session for testing
def override_get_session():
    with Session(engine) as session:
        yield session

# Override the session dependency to use the SQLite database instead of PostgreSQL
app.dependency_overrides[get_session] = override_get_session

# Create database and tables for the test
def create_test_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Test client for FastAPI
client = TestClient(app)

# Example test data directory
current_dir = Path(__file__).resolve().parent
example_data_dir = current_dir / "Example_data"

# Base URL for the API
BASE_URL = "http://data-annotation.k8s.synthema.rid-intrasoft.eu:80"  # Adjust the port if needed

# Test functions for CRUD operations

def test_healthcheck():
    response = client.get(f"{BASE_URL}/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_dataset_info():
    create_test_db_and_tables()  # Ensure the database is set up before running the test
    
    # Define the dataset info
    dataset_info = {
        "node": "node1",
        "path": "/path/to/data",
        "disease": "disease1"
    }
    
    # Send the POST request to create the dataset info
    response = client.post(f"{BASE_URL}/metadata", json=dataset_info)
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert response.json() == {"message": "Metadata uploaded successfully"}

def test_get_dataset_info():
    # Retrieve the dataset info using the API
    #response = client.get(f"{BASE_URL}/metadata/disease?node=node1&disease=disease1")
    response = client.get(f"{BASE_URL}/metadata?node=node1&disease=disease1")
    assert response.status_code == 200
    data = response.json()
    assert data["node"] == "node1"
    assert data["disease"] == "disease1"
    assert data["path"] == "/path/to/data"

#def test_update_dataset_info():
    # Update the dataset info
#    updated_dataset_info = {
#        "node": "node1",
#        "path": "/updated/path/to/data",
#        "disease": "disease1"
#    }

    # PUT request to update the dataset info
#    response = client.put(f"{BASE_URL}/metadata", json=updated_dataset_info)
#    assert response.status_code == 200
#    assert response.json() == {"message": "Metadata updated successfully"}

def test_delete_dataset_info():
    # Define the object to be deleted
    dataset_info_to_delete = {
        "node": "node1",
        "disease": "disease1",
        "path": "/updated/path/to/data"
    }

    # Delete the dataset info using the API
    #response = client.delete(f"{BASE_URL}/metadata", json=dataset_info_to_delete)
    response = client.delete(f"{BASE_URL}/metadata", data=json.dumps(dataset_info_to_delete), headers={"Content-Type": "application/json"})
    assert response.status_code == 200
    assert response.json() == {"message": "Dataset '/updated/path/to/data' deleted successfully."}

if __name__ == "__main__":
    # Run the tests sequentially
    test_healthcheck()
    test_create_dataset_info()
    test_get_dataset_info()
    test_update_dataset_info()
    test_delete_dataset_info()
