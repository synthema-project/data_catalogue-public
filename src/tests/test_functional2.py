from models import NodeDatasetInfo

def test_save_dataset_info_to_database_endpoint(client):
    # Define the payload to send to the API
    payload = {
        "node": "node1",
        "path": "/path/to/data",
        "disease": "disease1"
    }

    # Post to the /metadata endpoint
    response = client.post("/metadata", json=payload)

    # Verify the response
    assert response.status_code == 200
    assert response.json() == {"message": "Metadata uploaded successfully"}

def test_retrieve_dataset_info(client, session):
    # Add a dataset directly to the session for testing
    dataset = NodeDatasetInfo(node="node1", path="/path/to/data", disease="disease1")
    session.add(dataset)
    session.commit()

    # Retrieve the dataset using the API
    response = client.get("/metadata/disease?node=node1&disease=disease1")
    
    # Verify the response
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "node": "node1",
        "path": "/path/to/data",
        "disease": "disease1"
    }

def test_delete_dataset(client, session):
    # Add a dataset for testing
    dataset = NodeDatasetInfo(node="node1", path="/path/to/data", disease="disease1")
    session.add(dataset)
    session.commit()

    # Define the payload to delete the dataset
    payload = {
        "node": "node1",
        "disease": "disease1",
        "path": "/path/to/data"
    }

    # Delete the dataset using the API
    response = client.delete("/metadata", json=payload)

    # Verify the response
    assert response.status_code == 200
    assert response.json() == {"message": "Dataset '/path/to/data' deleted successfully."}

def test_get_all_datasets(client, session):
    # Add datasets for testing
    dataset1 = NodeDatasetInfo(node="node1", path="/path1", disease="disease1")
    dataset2 = NodeDatasetInfo(node="node2", path="/path2", disease="disease2")
    session.add(dataset1)
    session.add(dataset2)
    session.commit()

    # Retrieve all datasets using the API
    response = client.get("/metadata")

    # Verify the response
    assert response.status_code == 200
    assert len(response.json()["datasets"]) == 2
