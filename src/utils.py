from sqlmodel import Session, select
from fastapi import HTTPException
from models import NodeDatasetInfo, SyntheticDatasetGenerationRequestStatus, SyntheticDatasetGenerationRequestStatusTable
import logging
from typing import Tuple, Literal

from config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#def save_dataset_info_to_database(session: Session, node_dataset: NodeDatasetInfo):
#    try:
#        session.add(node_dataset)
#        session.commit()
#    except Exception as e:
#        print("Error saving dataset info to database:", e)
#        raise HTTPException(status_code=500, detail="Internal Server Error")

def save_dataset_info_to_database(session: Session, node_dataset: NodeDatasetInfo):
    try:
        logger.info(f"Adding dataset info for node: {node_dataset.node}, disease: {node_dataset.disease}")
        session.add(node_dataset)
        session.commit()
        logger.info(f"Dataset info saved successfully for node: {node_dataset.node}")
    except Exception as e:
        logger.error(f"Error saving dataset info to database: {str(e)}")
        session.rollback()  # Rollback in case of error
        raise HTTPException(status_code=500, detail="Internal Server Error")

def get_dataset_info_from_database(session: Session, node: str, disease: str):
    try:
        statement = select(NodeDatasetInfo).where(NodeDatasetInfo.node == node, NodeDatasetInfo.disease == disease)
        dataset_info = session.exec(statement).first()
        if dataset_info is None:
            raise HTTPException(status_code=404, detail=f"No dataset found in the database for node: {node} and disease: {disease}")
        return dataset_info
    except Exception as e:
        print("Error retrieving dataset info from database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

def remove_dataset_info_from_database(session: Session, node: str, disease: str, path: str) -> bool:
    try:
        # Fetch the dataset info
        statement = select(NodeDatasetInfo).where(
            NodeDatasetInfo.node == node,
            NodeDatasetInfo.disease == disease,
            NodeDatasetInfo.path == path
        )
        dataset_info = session.exec(statement).first()
        # Log the dataset info for debugging
        print("Dataset info found for deletion:", dataset_info)
        if dataset_info:
            # Perform deletion
            session.delete(dataset_info)
            session.commit()
            print("Dataset metadata successfully removed.")
            return True
        print("Dataset metadata not found in the database.")
        return False
    except Exception as e:
        print("Error removing dataset metadata:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

def remove_all_datasets_from_database(session: Session):
    try:
        statement = select(NodeDatasetInfo)
        datasets = session.exec(statement).all()
        for dataset in datasets:
            session.delete(dataset)
        session.commit()
    except Exception as e:
        print("Error removing all datasets from database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def fetch_all_datasets(session: Session):
    try:
        statement = select(NodeDatasetInfo)
        rows = session.exec(statement).all()
        datasets = [row.dict() for row in rows]
        return datasets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def register_new_sdg_task(
        task: SyntheticDatasetGenerationRequestStatus,
        session: Session,
        ) -> Tuple[str, str]:
    """
    Registers a new SD inference task in the storage.
    Assigns "running" status by default.

    Args:
        sdg_request_status (SyntheticDatasetGenerationRequestStatus):
            Task description.

    Returns:
        task_id (str): ID created by PostgreSQL for the new task.
        created_at (str): Timestamp for the new task registration.
    """

    try:
        # Transform task representation to match table structure
        task = SyntheticDatasetGenerationRequestStatusTable(**vars(task))
        session.add(task)
        session.commit()
        session.refresh(task)

        return str(task.task_id), str(task.created_at.isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def update_sdg_task_status(
    task_id: str,
    status: Literal["pending", "running", "cancelled", "success", "failed"],
    session: Session,
) -> None:
    """
    Updates the status of an SD inference task that was previously registered.
    The endpoint is called during the whole flow in the Shareable Data Pipeline (T3.1).
    Error status is also defined for tasks that fail during the process.

    Args:
        task_id (str): Inference task reference.
        status (Literal): Pending, running, cancelled, success, failed.

    Returns:
        None.
    """

    try:
        task = session.exec(select(SyntheticDatasetGenerationRequestStatusTable).where(
            SyntheticDatasetGenerationRequestStatusTable.task_id == task_id
        )).first()

        if task:
            task.status = status
            session.commit()
        else:
            HTTPException(status_code=404, detail=f"Task ID not found.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_sdg_task_status(task_id: str, session: Session) -> str:
    """
    Gets the status of a given task_id.

    Args:
        task_id (str): Inference task reference.

    Returns:
        status (str): Status of the task with ID task_id.
    """

    try:
        query = select(SyntheticDatasetGenerationRequestStatusTable.status).where(
            SyntheticDatasetGenerationRequestStatusTable.task_id == task_id)
        
        status_info = session.exec(query).first()
        if status_info is None:
            raise HTTPException(status_code=404, detail=f"Task ID not found.")
        else:
            return status_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
