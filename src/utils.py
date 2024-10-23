from sqlmodel import Session, select
from fastapi import HTTPException
from models import NodeDatasetInfo
import logging

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
        session.add(node_dataset.model_dump())
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
