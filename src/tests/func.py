# tests/func.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_post_metadata():
    payload = {
        "node":"n1",
        "path":"file.csv",
        "use_case":"covid",
        "num_records":2,
        "num_features":1,
        "data_schema":{"a":"int"},
        "dataset_metadata":{"title":"test"}
    }

    r = client.post("/metadata", json=payload)
    assert r.status_code == 200


def test_get_all_metadata():
    r = client.get("/metadata")
    assert r.status_code in (200,404)
