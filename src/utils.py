from sqlmodel import Session, select
from fastapi import HTTPException
from models import NodeDatasetInfo, SyntheticDatasetGenerationRequestStatus
import logging
from typing import Tuple, Literal
import psycopg2

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
        statement = select(NodeDatasetInfo).where(NodeDatasetInfo.node == node, NodeDatasetInfo.disease == disease, NodeDatasetInfo.path == path)
        dataset_info = session.exec(statement).first()
        print('DATASET-INFO', dataset_info)
        if dataset_info:
            session.delete(dataset_info)
            session.commit()
            return True
        return False
    except Exception as e:
        print("Error removing dataset info from database:", e)
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
        task: SyntheticDatasetGenerationRequestStatus
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
        # Create connection with PostgreSQL
        conn = psycopg2.connect(
            dbname=str(Settings.POSTGRES_DB),
            user=str(Settings.POSTGRES_USER),
            password=str(Settings.POSTGRES_PASSWORD),
            host=str(Settings.POSTGRES_HOST),
        )

        cursor = conn.cursor()

        # Insert new task in PostgreSQL
        try:
            cursor.execute(
                """
                INSERT INTO task_center (username, model, n_sample, disease, condition, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING task_id, created_at;
            """,
                (
                    str(task.user),
                    str(task.model),
                    int(task.n_sample),
                    str(task.disease),
                    str(task.condition),
                    "running",
                ),
            )

            task_id, created_at = cursor.fetchone()

            conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"SQL execution error: {e}")
            raise
        finally:
            cursor.close()

    except psycopg2.OperationalError as e:
        logger.error(f"Database connection error: {e}")
        raise

    finally:
        if conn:
            conn.close()

    return task_id, created_at


async def update_sdg_task_status(
    task_id: str,
    status: Literal["pending", "running", "cancelled", "success", "failed"],
):
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
        # Create connection with PostgreSQL
        conn = psycopg2.connect(
            dbname=str(Settings.POSTGRES_DB),
            user=str(Settings.POSTGRES_USER),
            password=str(Settings.POSTGRES_PASSWORD),
            host=str(Settings.POSTGRES_HOST),
        )

        cursor = conn.cursor()

        # Execute UPDATE task
        try:
            cursor.execute(
                """
                UPDATE task_center
                SET status = %s
                WHERE task_id = %s
            """,
                (str(status), str(task_id)),
            )
            conn.commit()

            # Check if any value was modified
            if cursor.rowcount > 0:
                print(f"Task {task_id} was updated.")
            else:
                print("No task was updated.")
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"SQL execution error: {e}")
            raise
        finally:
            cursor.close()

    except psycopg2.OperationalError as e:
        logger.error(f"Database connection error: {e}")
        raise

    finally:
        if conn:
            conn.close()

async def get_sdg_task_status(task_id: str):
    """
    Gets the status of a given task_id.

    Args:
        task_id (str): Inference task reference.

    Returns:
        status (str): Status of the task with ID task_id.
    """

    try:
        # Create connection with PostgreSQL
        conn = psycopg2.connect(
            dbname=str(Settings.POSTGRES_DB),
            user=str(Settings.POSTGRES_USER),
            password=str(Settings.POSTGRES_PASSWORD),
            host=str(Settings.POSTGRES_HOST),
        )

        cursor = conn.cursor()

        # Get status
        try:
            cursor.execute(
                """
                SELECT status
                FROM task_center
                WHERE task_id = %s
            """,
                (
                    str(task_id),
                ),
            )

            status = cursor.fetchone()

            conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"SQL execution error: {e}")
            raise
        finally:
            cursor.close()

    except psycopg2.OperationalError as e:
        logger.error(f"Database connection error: {e}")
        raise

    finally:
        if conn:
            conn.close()

    return status[0]
