# tests/func.py
import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    # if you have a reset method use it, otherwise drop manually
    yield


def test_add_and_list_use_cases():
    with patch("services.catalogue_service.remove_dataset_info_from_database", return_value=True):
        # Simulate an ingestion notification
        response = client.post(
            "/catalogue",
            json={
                "path": "file1.csv",
                "use_case": "aml1",
                "node": "NODE1"
            }
        )
        assert response.status_code == 200

    list_response = client.get("/use-cases")
    assert list_response.status_code == 200

    items = list_response.json()
    assert len(items) == 1
    assert items[0]["use_case"] == "aml1"
    assert "NODE1" in items[0]["datasets"]
