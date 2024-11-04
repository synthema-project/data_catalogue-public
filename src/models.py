from sqlmodel import SQLModel, Field
from pydantic import BaseModel

class NodeDatasetInfo(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    node: str
    path: str
    disease: str

class RemoveDatasetObject(BaseModel):
    node: str
    disease: str
    path: str

class SyntheticDatasetGenerationRequestStatus(BaseModel):
    user: str
    model: str
    n_sample: int
    disease: str
    condition: str
