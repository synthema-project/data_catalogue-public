from sqlmodel import SQLModel, Field
from pydantic import BaseModel
import uuid as uuid_pkg
from enum import Enum
from datetime import datetime
from typing import Optional

class NodeDatasetInfo(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    node: str
    path: str
    disease: str

class RemoveDatasetObject(BaseModel):
    node: str
    disease: str
    path: str

class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    cancelled = "cancelled"
    failed = "failed"

class SyntheticDatasetGenerationRequestStatus(BaseModel):
    username: str
    model: str
    n_sample: int
    disease: str
    condition: str

class SyntheticDatasetGenerationRequestStatusTable(
    SQLModel,
    SyntheticDatasetGenerationRequestStatus,
    table=True,
):
    __tablename__ = "task_center"
    task_id: Optional[uuid_pkg.UUID] = Field(default_factory=uuid_pkg.uuid4,
                                             primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    status: Optional[TaskStatus] = Field(default=TaskStatus.pending)
