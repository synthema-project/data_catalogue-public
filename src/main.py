from fastapi import FastAPI, HTTPException, Request, Depends, Body
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
#async def save_dataset_info_to_database_endpoint(node : str, disease : str, path : str, session: Session = Depends(get_session)):
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

#@app.delete("/metadata", tags=["data-catalogue"])
#async def delete_dataset(
#    #removedatasetobject: RemoveDatasetObject, 
#    #removedatasetobject: RemoveDatasetObject = Body(..., description="Dataset details in JSON format"),
#    node : str,
#    disease : str, 
#    path : str,
#    #request: Request, 
#    session: Session = Depends(get_session)
#):
#    #logging.info(f"Received request: {await request.json()}")
#    logging.info(f"Received query parameters: node={node}, disease={disease}, path={path}")
#    removedatasetobject = RemoveDatasetObject(node = node, disease = disease, path = path)
#    try:
#        result = remove_dataset_info_from_database(session, node=removedatasetobject.node, disease=removedatasetobject.disease, path=removedatasetobject.path)
#        if result:
#            logging.info(f"Metadata for path={path} removed successfully.")
#            return {"message": f"Dataset '{removedatasetobject.path}' deleted successfully."}
#        else:
#            raise HTTPException(status_code=404, detail=f"Dataset '{removedatasetobject.path}' not found.")
#    except HTTPException as e:
#        logger.error(f"HTTPException: {e.detail}")
#        raise e
#    except Exception as e:
#        logging.error(f"An error occurred: {e}")
#        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/metadata", tags=["data-catalogue"])
async def delete_dataset(
    node: str,
    disease: str,
    path: str,
    session: Session = Depends(get_session)
):
    try:
        # Log the incoming DELETE request
        logging.info(f"DELETE request received with node={node}, disease={disease}, path={path}")
        
        # Call the remove function
        result = remove_dataset_info_from_database(session, node=node, disease=disease, path=path)

        if result:
            logging.info(f"Metadata for path={path} removed successfully.")
            return {"message": f"Dataset '{path}' deleted successfully."}

        logging.warning(f"Metadata for path={path} not found in the database.")
        raise HTTPException(status_code=404, detail=f"Dataset '{path}' not found.")
    except Exception as e:
        logging.error(f"Error processing DELETE request: {e}")
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
async def request_synthetic_data_generation(
    sdg_request_status: SyntheticDatasetGenerationRequestStatus,
    session: Session = Depends(get_session)) -> Dict:

    """
    Calls the function that first registers a new task in the storage.

    Args:
        sdg_request_status (SyntheticDatasetGenerationRequestStatus):
            Task description.

    Returns:
        Log message.
    """

    try:
        task_id, created_at = await register_new_sdg_task(sdg_request_status,
                                                          session)

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
                                                   session: Session = Depends(get_session),
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
        await update_sdg_task_status(task_id, status, session)
    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"message": f"Task {task_id} - Status {status}"}

@app.get("/synthetic_data/generation_request", tags=['data-catalogue'])
async def get_synthetic_data_generation_request(task_id: str,
                                                session: Session = Depends(get_session)):
    """
    Calls the function that gets the status of a given task_id.

    Args:
        task_id (str): Inference task reference.

    Returns:
        Log message.
    """

    try:
        status = await get_sdg_task_status(task_id, session)
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
