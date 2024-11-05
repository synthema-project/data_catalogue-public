from fastapi import FastAPI, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from models import NodeDatasetInfo, RemoveDatasetObject, SyntheticDatasetGenerationRequestStatus
from utils import save_dataset_info_to_database, get_dataset_info_from_database, remove_dataset_info_from_database, fetch_all_datasets, remove_all_datasets_from_database
from utils import register_new_sdg_task, update_sdg_task_status, get_sdg_task_status
from database import create_db_and_tables, get_session
import uvicorn
import logging
from typing import Dict, Literal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

#@app.post("/metadata", tags=["data-catalogue"])
#async def save_dataset_info_to_database_endpoint(node_dataset: NodeDatasetInfo, session: Session = Depends(get_session)):
#    try:
#        save_dataset_info_to_database(session, node_dataset)
#        return {"message": 'Metadata uploaded successfully'}
#    except HTTPException as e:
#        raise e

@app.post("/metadata", tags=["data-catalogue"])
async def save_dataset_info_to_database_endpoint(node_dataset: NodeDatasetInfo, session: Session = Depends(get_session)):
    try:
        logger.info(f"Saving dataset info to the database for node: {node_dataset.node}, disease: {node_dataset.disease}")
        save_dataset_info_to_database(session, node_dataset)
        return {"message": 'Metadata uploaded successfully'}
    except HTTPException as e:
        logger.error(f"HTTPException occurred: {str(e)}")
        raise e
    except Exception as e:
        logger.exception("Unexpected error while saving dataset info to the database")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/metadata/{disease}", tags=["data-catalogue"])
async def retrieve_dataset_info(node: str, disease: str, session: Session = Depends(get_session)):
    try:
        dataset_info = get_dataset_info_from_database(session, node, disease)
        return dataset_info.dict()
    except HTTPException as e:
        raise e

@app.get("/metadata", tags=["data-catalogue"])
async def get_all_datasets(session: Session = Depends(get_session)):
    datasets = await fetch_all_datasets(session)
    if not datasets:
        raise HTTPException(status_code=404, detail="No datasets found")
    return {"datasets": datasets}

@app.delete("/metadata", tags=["data-catalogue"])
async def delete_dataset(removedatasetobject: RemoveDatasetObject, request: Request, session: Session = Depends(get_session)):
    logging.info(f"Received request: {await request.json()}")
    try:
        result = remove_dataset_info_from_database(session, node=removedatasetobject.node, disease=removedatasetobject.disease, path=removedatasetobject.path)
        if result:
            return {"message": f"Dataset '{removedatasetobject.path}' deleted successfully."}
        else:
            raise HTTPException(status_code=404, detail=f"Dataset '{removedatasetobject.path}' not found.")
    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/metadata/all", tags=["data-catalogue"])
async def delete_all_datasets(session: Session = Depends(get_session)):
    try:
        remove_all_datasets_from_database(session)
        return {"message": "All datasets deleted successfully."}
    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/synthetic_data/generation_request", tags=["data-catalogue"])
async def request_synthetic_data_generation(sdg_request_status: SyntheticDatasetGenerationRequestStatus,
                                            ) -> Dict:
    """
    Calls the function that first registers a new task in the storage.

    Args:
        sdg_request_status (SyntheticDatasetGenerationRequestStatus):
            Task description.

    Returns:
        Log message.
    """

    try:
        task_id, created_at = await register_new_sdg_task(sdg_request_status)

        return {
            "message": "Task was succesfully sent.",
            "task_id": str(task_id),
            "created_at": str(created_at),
        }

    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.put("/synthetic_data/generation_request", tags=["data-catalogue"])
async def update_synthetic_data_generation_request(task_id: str,
                                                   status: Literal["pending", "running", "cancelled", "success", "failed"],
                                                   ) -> Dict:
    """
    Calls the function that updates the  status of a previously
    registered task.

    Args:
        task_id (str): Inference task reference.
        status (Literal): Pending, running, cancelled, success, failed.

    Returns:
        Log message.
    """

    try:
        update_sdg_task_status(task_id, status)
    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"message": f"Task {task_id} - Status {status}"}

@app.get("/synthetic_data/generation_request", tags=['data-catalogue'])
async def get_synthetic_data_generation_request(task_id: str):
    """
    Calls the function that gets the status of a given task_id.

    Args:
        task_id (str): Inference task reference.

    Returns:
        Log message.
    """

    try:
        status = await get_sdg_task_status(task_id)
    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"message": f"Checked task ID {task_id}",
            "status": f"{status}"}

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=83)
