from pathlib import Path
from fastapi.testclient import TestClient
from main import app
from models import NodeDatasetInfo, RemoveDatasetObject

client = TestClient(app)

# Get the directory path of the current script
current_dir = Path(__file__).resolve().parent

# Sample data for testing
node_dataset = {
    "id": 1,
    "node": "Node1",
    "path": "/path/to/data",
    "disease": "Disease1"
}

remove_dataset = {
    "node": "Node1",
    "disease": "Disease1",
    "path": "/path/to/data"
}


def test_save_dataset_info():
    # Test the endpoint for saving dataset info
    response = client.post("/metadata", json=node_dataset)
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert response.json() == {"message": 'Metadata uploaded successfully'}, "Failed to upload dataset info"


def test_get_dataset_info():
    # Test the endpoint for retrieving a dataset by disease
    response = client.get(f"/metadata/{node_dataset['disease']}?node={node_dataset['node']}")
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    data = response.json()
    assert data["node"] == node_dataset["node"], "Node mismatch in retrieved dataset"
    assert data["disease"] == node_dataset["disease"], "Disease mismatch in retrieved dataset"
    assert data["path"] == node_dataset["path"], "Path mismatch in retrieved dataset"


def test_get_all_datasets():
    # Test the endpoint for retrieving all datasets
    response = client.get("/metadata")
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert "datasets" in response.json(), "Failed to retrieve all datasets"
    assert any(dataset["disease"] == node_dataset["disease"] for dataset in response.json()["datasets"]), "No matching datasets found"


def test_delete_dataset():
    # Test the endpoint for deleting a specific dataset
    response = client.delete("/metadata", json=remove_dataset)
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert response.json() == {"message": f"Dataset '{remove_dataset['path']}' deleted successfully."}, "Failed to delete dataset"


def test_delete_all_datasets():
    # Test the endpoint for deleting all datasets
    response = client.delete("/metadata/all")
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert response.json() == {"message": "All datasets deleted successfully."}, "Failed to delete all datasets"


def test_healthcheck():
    # Test the healthcheck endpoint
    response = client.get("/healthcheck")
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response content: {response.content.decode()}"
    assert response.json() == {"status": "ok"}, "Healthcheck failed"


# Additional test cases can be added here as needed
