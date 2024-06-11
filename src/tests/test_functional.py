from fastapi.testclient import TestClient
from main import app, create_connection
from data_catalogue_utils import DATABASE_FILE
import os

client = TestClient(app)

def setup_module(module):
    # Setup database before tests
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node TEXT NOT NULL,
            path TEXT NOT NULL,
            disease TEXT NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def teardown_module(module):
    # Teardown database after tests
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)

def test_save_dataset_info():
    response = client.post("/metadata", json={"node": "NODE1", "path": "./NODE1", "disease": "AML"})
    assert response.status_code == 200
    assert response.json() == {"message": "Metadata uploaded successfully"}

def test_retrieve_dataset_info():
    client.post("/metadata", json={"node": "NODE1", "path": "./NODE1", "disease": "AML"})
    response = client.get("/metadata/AML", params={"node": "NODE1"})
    assert response.status_code == 200
    data = response.json()
    assert data["node"] == "NODE1"
    assert data["path"] == "./NODE1"
    assert data["disease"] == "AML"

def test_get_all_datasets():
    client.post("/metadata", json={"node": "NODE1", "path": "./NODE1", "disease": "AML"})
    response = client.get("/metadata")
    assert response.status_code == 200
    datasets = response.json()["datasets"]
    assert len(datasets) > 0

def test_delete_dataset(client):
    client.post("/metadata", json={"node": "NODE1", "path": "./NODE1", "disease": "AML"})
    response = client.delete("/metadata", params={"node": "NODE1", "disease": "AML", "path": "./NODE1"})
    assert response.status_code == 200
    assert response.json() == {"message": "Dataset './NODE1' deleted successfully."}
    response = client.get("/metadata/AML", params={"node": "NODE1"})
    assert response.status_code == 404
