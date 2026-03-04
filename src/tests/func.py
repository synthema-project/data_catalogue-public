# tests/func.py
from fastapi.testclient import TestClient
from main import app

from main import app, get_session
from sqlmodel import Session
from unittest.mock import MagicMock

def fake_session():
    return MagicMock(spec=Session)

app.dependency_overrides[get_session] = fake_session

client = TestClient(app)

def test_post_metadata():
    payload = {
    "node":"n1",
    "path":"file.csv",
    "use_case":"covid",
    "num_records":2,
    "num_features":1,
    "schema":{"a":["int"]},
    "metadata":{"title":"test"}
}

    r = client.post("/metadata", json=payload)
    assert r.status_code == 200


def test_get_all_metadata():
    r = client.get("/metadata")
    assert r.status_code in (200,404)
