import pytest
from data_catalogue_utils import create_connection, save_dataset_info_to_database, get_dataset_info_from_database, remove_dataset_info_from_database, NodeDatasetInfo

DATABASE_FILE = "./test_central_node.db"

@pytest.fixture
def setup_database():
    # Create a temporary database for testing
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
    yield conn
    cursor.execute("DROP TABLE datasets")
    conn.close()

def test_create_connection(setup_database):
    conn = create_connection()
    assert conn is not None

def test_save_dataset_info_to_database(setup_database):
    node_dataset = NodeDatasetInfo(node="test_node", path="test_path", disease="test_disease")
    save_dataset_info_to_database(node_dataset)
    conn = setup_database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets WHERE node=? AND path=? AND disease=?", 
                   (node_dataset.node, node_dataset.path, node_dataset.disease))
    result = cursor.fetchone()
    assert result is not None

def test_get_dataset_info_from_database(setup_database):
    node_dataset = NodeDatasetInfo(node="test_node", path="test_path", disease="test_disease")
    save_dataset_info_to_database(node_dataset)
    dataset_info = get_dataset_info_from_database(node="test_node", disease="test_disease")
    assert dataset_info is not None
    assert dataset_info[0] == "test_node"

def test_remove_dataset_info_from_database(setup_database):
    node_dataset = NodeDatasetInfo(node="test_node", path="test_path", disease="test_disease")
    save_dataset_info_to_database(node_dataset)
    result = remove_dataset_info_from_database(node="test_node", disease="test_disease", path="test_path")
    assert result is True
    dataset_info = get_dataset_info_from_database(node="test_node", disease="test_disease")
    assert dataset_info is None
