from sqlmodel import SQLModel, Field, JSON
from pydantic import BaseModel
import uuid as uuid_pkg
from enum import Enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, JSON as JSONType
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from typing import Dict, Any

from sqlalchemy import Column, String

class NodeDatasetInfo(SQLModel, table=True, __tablename__="data_catalogue"):
    #id: str = Field(default=None, primary_key=True)
    #id: Optional[int] = Field(default=None, primary_key=True)
    id: Optional[uuid_pkg.UUID] = Field(default_factory=uuid_pkg.uuid4,
                                             primary_key=True)
    node: str
    path: str
    use_case: str # to change into use_case

#class UseCase(SQLModel, table=True):
#    __tablename__ = "usecases"
#
#    use_case: str = Field(primary_key=True)
#    nodes: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))

#class UseCase(SQLModel, table=True):
#    __tablename__ = "usecases"
#    use_case: str = Field(primary_key=True)
#    datasets: list = Field(sa_column=Column(JSONB))

#class UseCase(SQLModel, table=True):
#    use_case: str = Field(primary_key=True)
#    datasets: list[dict] = Field(
#        default_factory=list,
#        sa_column=Column(JSON)
#    )

class UseCase(SQLModel, table=True):
    __tablename__ = "usecases"

    use_case: str = Field(primary_key=True)

    # Postgres ARRAY of JSONB objects
    datasets: List[Dict[str, Any]] = Field(
        sa_column=Column(ARRAY(JSONB), nullable=False, default=list)
    )

class UseCase(SQLModel, table=True):
    __tablename__ = "usecases"

    use_case: str = Field(primary_key=True)
    datasets: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))

class RemoveDatasetObject(BaseModel):
    node: str
    use_case: str # to change into use_case
    path: str

class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    cancelled = "cancelled"
    failed = "failed"
    
class FilterInput(BaseModel):
    column: str
    operator: str = "="
    filter_value: str

class SyntheticDatasetGenerationRequestStatus(BaseModel):
    username: str
    model: str
    n_sample: int
    disease: str
    filters: List[FilterInput] = Field(default_factory=list)

class SyntheticDatasetGenerationRequestStatusTable(
    SQLModel,
    SyntheticDatasetGenerationRequestStatus,
    table=True,
):
    __tablename__ = "request_center"
    task_id: Optional[uuid_pkg.UUID] = Field(default_factory=uuid_pkg.uuid4,
                                             primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    status: Optional[TaskStatus] = Field(default=TaskStatus.pending)
    queried_data_uri: Optional[str] = Field(default=None)

    filters: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column("filters", JSONType),
        repr=False,
    )
    
    @classmethod
    def convert_to_db_entry(cls, req: SyntheticDatasetGenerationRequestStatus) -> "SyntheticDatasetGenerationRequestStatusTable":
        """Construct the row for db from the API input model"""
        return cls(
            username=req.username,
            model=req.model,
            n_sample=req.n_sample,
            disease=req.disease,
            # Convertimos objetos FilterInput -> dicts JSON
            filters=[f.model_dump() for f in (req.filters or [])],

        )













