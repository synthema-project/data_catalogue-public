from sqlmodel import Session, select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import NodeDatasetInfo, UseCase, SyntheticDatasetGenerationRequestStatus, SyntheticDatasetGenerationRequestStatusTable as SDGRT
import logging
from typing import Tuple, Literal, Optional, List
from enum import Enum

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

def save_dataset_info_to_database(
    session: Session, 
    node_dataset: NodeDatasetInfo
):
    try:
        #logger.info(f"Adding dataset info for node: {node_dataset.node}, disease: {node_dataset.disease}")
        logger.info(f"Adding dataset info for node={node_dataset.node}, use_case={node_dataset.use_case}")
        session.add(node_dataset)
        session.commit()
        logger.info(f"Dataset info saved successfully for node: {node_dataset.node}")
    except Exception as e:
        logger.error(f"Error saving dataset info to database: {str(e)}")
        session.rollback()  # Rollback in case of error
        raise HTTPException(status_code=500, detail="Internal Server Error")
'''
def update_use_case(
    session: Session,
    use_case: str,
    node: str,
    path: str
):
    """Register that a given node contains data for a use-case."""

    try:
        uc = session.get(UseCase, use_case)
        entry = {"node": node, "path": path}
        if uc is None:
            uc = UseCase(use_case=use_case, datasets=[entry])
            session.add(uc)
        else:
            if node not in uc.nodes:
                uc.nodes.append(entry)

        session.commit()
        logger.info(f"Use-case {use_case} updated with node {node}")

    except Exception as e:
        session.rollback()
        logger.error(f"Error updating use-case: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
'''
def update_use_case(session: Session, use_case: str, node: str, path: str):
    """
    Add dataset (node + path) to a use-case.
    """
    try:
        uc = session.get(UseCase, use_case)

        dataset_entry = {"node": node, "path": path}

        if uc is None:
            # Create new use-case record
            uc = UseCase(
                use_case=use_case,
                datasets=[dataset_entry]
            )
            session.add(uc)

        else:
            # Avoid duplicates
            if dataset_entry not in uc.datasets:
                uc.datasets.append(dataset_entry)

        session.commit()
        session.refresh(uc)

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating use-case: {e}")

#def get_dataset_info_from_database(
#    session: Session,
#    node: str, disease: str):
#    try:
#        statement = select(NodeDatasetInfo).where(NodeDatasetInfo.node == node, NodeDatasetInfo.disease == disease)
#        dataset_info = session.exec(statement).first()
#        if dataset_info is None:
#            raise HTTPException(status_code=404, detail=f"No dataset found in the database for node: {node} and disease: {disease}")
#        return dataset_info
#    except Exception as e:
#        print("Error retrieving dataset info from database:", e)
#        raise HTTPException(status_code=500, detail="Internal Server Error")

def get_dataset_info_from_database(session: Session, path: str):
    try:
        statement = select(NodeDatasetInfo).where(NodeDatasetInfo.path == path)
        dataset_info = session.exec(statement).first()
        if dataset_info is None:
            raise HTTPException(
                status_code=404,
                detail=f"No dataset found with path: {path}"
            )
        return dataset_info
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

#def remove_dataset_info_from_database(session: Session, node: str, disease: str, path: str) -> bool:
#    try:
#        # Fetch the dataset info
#        statement = select(NodeDatasetInfo).where(
#            NodeDatasetInfo.node == node,
#            NodeDatasetInfo.disease == disease,
#            NodeDatasetInfo.path == path #f"{node}/{filename}" ##path
#        )
#        logging.info(f"Trying to delete metadata: node={node}, disease={disease}, path={path}")
#        dataset_info = session.exec(statement).first()
#        # Log the dataset info for debugging
#        print("Dataset info found for deletion:", dataset_info)
#        if dataset_info:
#            # Perform deletion
#            session.delete(dataset_info)
#            session.commit()
#            print("Dataset metadata successfully removed.")
#            return True
#        print("Dataset metadata not found in the database.")
#        return False
#    except Exception as e:
#        print("Error removing dataset metadata:", e)
#        raise HTTPException(status_code=500, detail="Internal Server Error")

def remove_dataset_info_from_database(session: Session, path: str) -> bool:
    try:
        # Fetch dataset
        statement = select(NodeDatasetInfo).where(NodeDatasetInfo.path == path)
        dataset_info = session.exec(statement).first()

        if not dataset_info:
            return False

        use_case = dataset_info.use_case
        node = dataset_info.node

        # delete dataset entry
        session.delete(dataset_info)

        # update use-case table
        uc = session.get(UseCase, use_case)
        if uc:
            uc.datasets = [d for d in uc.datasets if d["path"] != path]

            if len(uc.datasets) == 0:
                session.delete(uc)

        session.commit()
        return True

    except Exception:
        session.rollback()
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
        task = SDGRT.convert_to_db_entry(task)
        session.add(task)
        session.commit()
        session.refresh(task)

        return str(task.task_id), str(task.created_at.isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def update_sdg_task_status(
    task_id: str,
    status: Literal["pending", "running", "cancelled", "success", "failed"],
    synthetic_data_uri: Optional[str],
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
        task = session.exec(select(SDGRT).where(
            SDGRT.task_id == task_id
        )).first()

        if task:
            task.status = status
            task.queried_data_uri = synthetic_data_uri
            session.commit()
        else:
            HTTPException(status_code=404, detail=f"Task ID not found.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_sdg_task_status(task_id: str, session: Session) -> Optional[str]:
    """
    Gets the status of a given task_id.

    Args:
        task_id (str): Inference task reference.

    Returns:
        status (str): Status of the task with ID task_id.
    """

    try:
        query = select(SDGRT.status).where(
            SDGRT.task_id == task_id)
        
        status_info = session.exec(query).first()
        if status_info is None:
            raise HTTPException(status_code=404, detail=f"Task ID not found.")
        else:
            return status_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    
    
async def get_sdg_task_uri(task_id: str, session: Session) -> str:
    """
    Gets the queried_data_uri of a given task_id.

    Args:
        task_id (str): Inference task reference.

    Returns:
        queried_data_uri (str): URI to download the queried data
    """
    
    try:
        query = select(SDGRT.queried_data_uri).where(
            SDGRT.task_id == task_id)
        
        data_uri = session.exec(query).first()
        return data_uri
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    
    
def normalize_filters(filters_str):
    if isinstance(filters_str, (str, bytes, bytearray)):
        try:
            return json.loads(filters_str)
        except Exception:
            return filters_str
        return filters_str
    
    
async def get_user_requests_list(username: str, session: Session) -> List[dict]:
    """
    Gets the requests list for a given user
    
    Args:
        username (str): Username

    Returns:
        user_requests (List[dict]): List of requests data with parameters
    """

    try:
        # Prepare query
        query = select(
            SDGRT.task_id,
            SDGRT.created_at,
            SDGRT.model,
            SDGRT.n_sample,
            SDGRT.disease,
            SDGRT.filters,
            SDGRT.status
        )
        query = query.where(SDGRT.username == username)
        query = query.order_by(SDGRT.created_at.desc()).limit(100).offset(0)
        
        # Execute query
        rows = session.exec(query).all()
        user_requests = [
            {
                "task_id": row[0],
                "created_at": row[1],
                "model": row[2],
                "n_samples": row[3],
                "disease": row[4],
                "filters": normalize_filters(filters_str=row[5]),
                "status": row[6].value if isinstance(row[6], Enum) else row[6],
            }
            for row in rows
        ]
        
        # Return results
        return user_requests
    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e)) from e









