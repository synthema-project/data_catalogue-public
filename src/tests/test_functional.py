from fastapi.testclient import TestClient
from main import app
from data_catalogue_utils import create_connection

client = TestClient(app)

def setup_module(module):
    # Setup database before tests
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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE datasets")
    conn.commit()
    cursor.close()
    conn.close()

def test_save_dataset_info():
    response = client.post("/metadata", json={"node": "test_node", "path": "test_path", "disease": "test_disease"})
    assert response.status_code == 200
    assert response.json() == {'Metadata uploaded successfully'}

def test_retrieve_dataset_info():
    client.post("/metadata", json={"node": "test_node", "path": "test_path", "disease": "test_disease"})
    response = client.get("/metadata/test_disease", params={"node": "test_node"})
    assert response.status_code == 200
    data = response.json()
    assert data["node"] == "test_node"
    assert data["path"] == "test_path"
    assert data["disease"] == "test_disease"

def test_get_all_datasets():
    client.post("/metadata", json={"node": "test_node", "path": "test_path", "disease": "test_disease"})
    response = client.get("/metadata")
    assert response.status_code == 200
    datasets = response.json()["datasets"]
    assert len(datasets) > 0

def test_delete_dataset():
    client.post("/metadata", json={"node": "test_node", "path": "test_path", "disease": "test_disease"})
    response = client.delete("/metadata", params={"node": "test_node", "disease": "test_disease", "path": "test_path"})
    assert response.status_code == 200
    assert response.json() == {"message": "Dataset 'test_path' deleted successfully."}
    response = client.get("/metadata/test_disease", params={"node": "test_node"})
    assert response.status_code == 404
