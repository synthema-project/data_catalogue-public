from fastapi import FastAPI, HTTPException, Request, Depends, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import delete
from models import NodeDatasetInfo, UseCase, RemoveDatasetObject, SyntheticDatasetGenerationRequestStatus
from utils import save_dataset_info_to_database, update_use_case, get_dataset_info_from_database, remove_dataset_info_from_database, fetch_all_datasets, remove_all_datasets_from_database
from utils import register_new_sdg_task, update_sdg_task_status, get_sdg_task_status, get_sdg_task_uri, get_user_requests_list
from utils import get_all_use_cases, get_single_use_case, delete_all_use_cases
from database import create_db_and_tables, get_session, add_datasets_column_to_usecases, add_new_metadata_columns, migrate_usecase_datasets_to_jsonb #add_use_case_column, 
from auth import UserClaims, require_authentication
import uvicorn
import logging
from typing import Dict, Literal, Optional
from sqlmodel import select

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
'''
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''
@app.on_event("startup")
def on_startup():
    add_new_metadata_columns()
    #add_use_case_column()
    add_datasets_column_to_usecases()
    migrate_usecase_datasets_to_jsonb()
    create_db_and_tables()

#@app.post("/metadata", tags=["data-catalogue"])
#async def save_dataset_info_to_database_endpoint(node_dataset: NodeDatasetInfo, session: Session = Depends(get_session)):
#    try:
#        save_dataset_info_to_database(session, node_dataset)
#        return {"message": 'Metadata uploaded successfully'}
#    except HTTPException as e:
#        raise e

@app.post("/metadata", tags=["data-catalogue"])
async def save_dataset_info_to_database_endpoint(
    node_dataset: NodeDatasetInfo, 
    session: Session = Depends(get_session),
    ##current_user: UserClaims = Depends(require_authentication)
):
#async def save_dataset_info_to_database_endpoint(node : str, disease : str, path : str, session: Session = Depends(get_session)):
    try:
        #logger.info(f"Saving dataset info to the database for node: {node_dataset.node}, disease: {node_dataset.disease}")
        logger.info(f"Saving metadata for node={node_dataset.node}, use_case={node_dataset.use_case}")
        
        # Save per-dataset metadata
        save_dataset_info_to_database(session, node_dataset)
        
        # Update the use-case aggregated structure
        #update_use_case(session, node_dataset.use_case, node_dataset.node)
        update_use_case(session, use_case=node_dataset.use_case, node=node_dataset.node, path=node_dataset.path)

        return {"message": 'Metadata uploaded successfully'}
    
    except HTTPException as e:
        logger.error(f"HTTPException occurred: {str(e)}")
        raise e
    except Exception as e:
        logger.exception("Unexpected error while saving dataset info to the database")
        raise HTTPException(status_code=500, detail="Internal Server Error")
'''
@app.get("/usecases", tags=["data-catalogue"])
async def get_use_cases(
    session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication)
):
    statement = select(UseCase)
    ucs = session.exec(statement).all()

    return {"use_cases": [uc.model_dump() for uc in ucs]}

@app.get("/usecases/{use_case}")
def get_use_case(
    use_case: str, 
    db: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication)
):
    record = db.query(UseCase).filter_by(use_case=use_case).first()

    if not record:
        raise HTTPException(status_code=404, detail="Use case not found")

    return {
        "use_case": record.use_case,
        "datasets": record.datasets
    }
'''
@app.get("/usecases", tags=["data-catalogue"])
async def get_use_cases(
    session: Session = Depends(get_session),
    ##current_user: UserClaims = Depends(require_authentication)
):
    use_cases = get_all_use_cases(session)
    return {"use_cases": [uc.model_dump() for uc in use_cases]}


@app.get("/usecases/{use_case}", tags=["data-catalogue"])
async def get_use_case(
    use_case: str,
    session: Session = Depends(get_session),
    ##current_user: UserClaims = Depends(require_authentication)
):
    record = get_single_use_case(session, use_case)

    return {
        "use_case": record.use_case,
        "datasets": record.datasets
    }


@app.delete("/usecases/all", tags=["data-catalogue"])
async def delete_all_usecases(
    session: Session = Depends(get_session),
    ##current_user: UserClaims = Depends(require_authentication)
):
    delete_all_use_cases(session)
    return {"detail": "All use-cases have been deleted"}



@app.get("/metadata/{disease}", tags=["data-catalogue"])
async def retrieve_dataset_info(
    node: str, 
    disease: str, 
    session: Session = Depends(get_session),
    ##current_user: UserClaims = Depends(require_authentication)
):
    try:
        dataset_info = get_dataset_info_from_database(session, node, disease)
        return dataset_info.dict()
    except HTTPException as e:
        raise e

@app.get("/metadata", tags=["data-catalogue"])
async def get_all_datasets(
    session: Session = Depends(get_session),
    ##current_user: UserClaims = Depends(require_authentication)
):
    datasets = await fetch_all_datasets(session)
    if not datasets:
        raise HTTPException(status_code=404, detail="No datasets found")
    return {"datasets": datasets}
'''
@app.delete("/usecases/all")
def delete_all_usecases(
    session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication)
):
    session.exec(delete(UseCase))
    session.commit()
    return {"All use-cases have been deleted"}
'''
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

#@app.delete("/metadata", tags=["data-catalogue"])
#async def delete_dataset(
#    node: str,
#    disease: str,
#    path: str,
#    session: Session = Depends(get_session)
#):
#    try:
#        # Log the incoming DELETE request
#        logging.info(f"DELETE request received with node={node}, disease={disease}, path={path}")
#        
#        # Call the remove function
#        result = remove_dataset_info_from_database(session, node=node, disease=disease, path=path)

#        if result:
#            logging.info(f"Metadata for path={path} removed successfully.")
#            return {"message": f"Dataset '{path}' deleted successfully."}

#        logging.warning(f"Metadata for path={path} not found in the database.")
#        raise HTTPException(status_code=404, detail=f"Dataset '{path}' not found.")
#    except Exception as e:
#        logging.error(f"Error processing DELETE request: {e}")
#        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/metadata", tags=["data-catalogue"])
async def delete_dataset(
    path: str,
    session: Session = Depends(get_session),
    ##current_user: UserClaims = Depends(require_authentication)
):
    try:
        result = remove_dataset_info_from_database(session, path=path)
        if result:
            return {"message": f"Dataset '{path}' deleted successfully."}

        raise HTTPException(status_code=404, detail=f"Dataset '{path}' not found.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/metadata/all", tags=["data-catalogue"])
async def delete_all_datasets(
    session: Session = Depends(get_session),
    ##current_user: UserClaims = Depends(require_authentication)
):
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
    session: Session = Depends(get_session)
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
        task_id, created_at = await register_new_sdg_task(sdg_request_status,
                                                          session)

        return {
            "message": "Task was succesfully sent.",
            "task_id": str(task_id),
            "created_at": str(created_at),
        }

    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.put("/synthetic_data/generation_request", tags=["data-catalogue"])
async def update_synthetic_data_generation_request(task_id: str,
                                                   status: Literal["pending", "running", "cancelled", "success", "failed"],
                                                   synthetic_data_uri: Optional[str] = None,
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
        await update_sdg_task_status(task_id, status, synthetic_data_uri, session)
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

    queried_data_uri = None
    
    try:
        status = await get_sdg_task_status(task_id, session)
        queried_data_uri = await get_sdg_task_uri(task_id, session)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    result = {
        "message": f"Checked task ID {task_id}",
        "status": f"{status}",
    }
    if queried_data_uri is not None:
        result["queried_data_uri"] = queried_data_uri
    return result


@app.get("/synthetic_data/user_generation_requests", tags=['data-catalogue'])
async def get_synthetic_data_user_generation_requests(
    username: str,
    session: Session = Depends(get_session)
):
    """
    Calls the function that gets the tasks list of a user.

    Args:
        username (str): Username who made the requests

    Returns:
        Log message.
    """
    
    try:
        requests_list = await get_user_requests_list(username, session)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    
    payload = {"username": username, "requests_count": len(requests_list), "requests_data": requests_list}

    return JSONResponse(content=jsonable_encoder(payload))



@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=83)







































