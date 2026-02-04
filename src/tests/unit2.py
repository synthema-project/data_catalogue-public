from models import NodeDatasetInfo

import pytest
from sqlmodel import SQLModel, Session, create_engine

@pytest.fixture
def session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

def test_node_dataset_creation():
    ds = NodeDatasetInfo(
        node="node1",
        path="file.csv",
        use_case="covid",
        num_records=10,
        num_features=2,
        data_schema={"a":"int"},
        dataset_metadata={"title":"t"}
    )

    assert ds.node == "node1"
    assert ds.dataset_metadata["title"] == "t"

from models import UseCase
from utils import update_use_case

def test_update_usecase_creates(session):
    update_use_case(session, "covid", "node1", "file.csv")

    uc = session.get(UseCase, "covid")
    assert "node1" in uc.datasets

from models import NodeDatasetInfo
from utils import save_dataset_info_to_database

def test_save_metadata(session):
    ds = NodeDatasetInfo(
        node="n1",
        path="f.csv",
        use_case="covid"
    )

    save_dataset_info_to_database(session, ds)

    result = session.get(NodeDatasetInfo, ds.id)
    assert result is not None
