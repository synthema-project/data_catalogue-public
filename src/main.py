from fastapi import FastAPI, HTTPException, Request, Depends, Body
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import delete
from models import NodeDatasetInfo, UseCase, RemoveDatasetObject, SyntheticDatasetGenerationRequestStatus, DatasetMetadata, UpdateSdgTaskBody
from utils import save_dataset_info_to_database, update_use_case, get_dataset_info_from_database, remove_dataset_info_from_database, fetch_all_datasets, remove_all_datasets_from_database
from utils import register_new_sdg_task, update_sdg_task_status, get_sdg_task_status, get_sdg_task_uri, get_user_requests_list
from utils import get_all_use_cases, get_single_use_case, delete_all_use_cases, delete_all_use_cases_and_datasets, remove_single_dataset_from_use_case
from database import create_db_and_tables, get_session, add_datasets_column_to_usecases, add_new_metadata_columns, migrate_usecase_datasets_to_jsonb, migrate_schema_and_metadata_columns #add_use_case_column, 
from auth import UserClaims, require_authentication
import uvicorn
import logging
from typing import Dict, Literal, Optional
from datetime import datetime
from sqlmodel import select

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    add_new_metadata_columns()
    #add_use_case_column()
    add_datasets_column_to_usecases()
    migrate_usecase_datasets_to_jsonb()
    migrate_schema_and_metadata_columns()

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
    current_user: UserClaims = Depends(require_authentication)
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
'''
@app.get("/usecases", tags=["data-catalogue"])
async def get_use_cases(
    session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication)
):
    use_cases = get_all_use_cases(session)
    return {"use_cases": [uc.model_dump() for uc in use_cases]}
'''
@app.get("/usecases", tags=["data-catalogue"])
async def get_use_cases(
    session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication)
):
    statement = select(UseCase)
    ucs = session.exec(statement).all()

    return {
        "use_cases": [
            {
                "use_case": uc.use_case,
                "datasets": uc.datasets   # ← IMPORTANT
            }
            for uc in ucs
        ]
    }


@app.get("/usecases/{use_case}", tags=["data-catalogue"])
async def get_use_case(
    use_case: str,
    session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication)
):
    record = get_single_use_case(session, use_case)

    return {
        "use_case": record.use_case,
        "datasets": record.datasets
    }


@app.delete("/usecases/all", tags=["data-catalogue"])
async def delete_all_usecases(
    session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication)
):
    delete_all_use_cases(session)
    return {"detail": "All use-cases have been deleted"}
'''
@app.delete("/usecases/all", tags=["data-catalogue"])
def delete_all_usecases(
    session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication)
):
    delete_all_use_cases_and_datasets(session)
    return {"detail": "All use-cases AND dataset metadata have been deleted"}
'''
@app.get("/metadata/{disease}", tags=["data-catalogue"])
async def retrieve_dataset_info(
    node: str, 
    disease: str, 
    session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication)
):
    try:
        dataset_info = get_dataset_info_from_database(session, node, disease)
        return dataset_info.dict()
    except HTTPException as e:
        raise e

@app.get("/metadata", tags=["data-catalogue"])
async def get_all_datasets(
    session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication)
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
    current_user: UserClaims = Depends(require_authentication)
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
    current_user: UserClaims = Depends(require_authentication)
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

# If you use app (not a router), add it to the same file:
@app.delete("/usecases/dataset", tags=["data-catalogue"])
def delete_dataset_from_use_case(
    dataset_path: str,
    session: Session = Depends(get_session),
    #current_user: UserClaims = Depends(require_authentication)
):
    removed = remove_single_dataset_from_use_case(session, dataset_path)

    if not removed:
        raise HTTPException(status_code=404, detail="Dataset not found in any use-case")

    return {"detail": "Dataset removed from use-case(s)"}


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
async def update_synthetic_data_generation_request(
    payload: UpdateSdgTaskBody = Body(...),
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
        await update_sdg_task_status(
            payload.task_id,
            payload.status,
            payload.synthetic_data_uri,
            session
        )
    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"message": f"Task {payload.task_id} - Status {payload.status}"}

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



# ============ Synthetic Data Pool Management Endpoints ============

@app.post("/synthetic-pools", tags=["synthetic-pools"])
async def register_synthetic_pool(
    use_case: str,
    sdg_model_name: str,
    pool_metadata: Dict,
    session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication),
):
    """Register a new synthetic data pool from client generation."""
    from models import SyntheticDataPool

    try:
        pool = SyntheticDataPool(
            use_case=use_case,
            sdg_model_name=sdg_model_name,
            node_name=pool_metadata.get("node_name", "unknown"),
            n_samples=pool_metadata.get("n_samples", 0),
            s3_uris=pool_metadata.get("s3_uris", {}),
            local_paths=pool_metadata.get("local_paths", {}),
            validation_reports=pool_metadata.get("validation_reports", {}),
            status="pending_approval"
        )
        session.add(pool)
        session.commit()
        session.refresh(pool)

        logger.info(f"Registered synthetic pool {pool.pool_id} for {use_case}")

        return {
            "pool_id": pool.pool_id,
            "use_case": pool.use_case,
            "status": pool.status,
            "created_at": pool.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to register synthetic pool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/synthetic-pools/{pool_id}", tags=["synthetic-pools"])
async def get_synthetic_pool(pool_id: str, session: Session = Depends(get_session), current_user: UserClaims = Depends(require_authentication)):
    """Retrieve details of a synthetic data pool."""
    from models import SyntheticDataPool

    try:
        pool = session.query(SyntheticDataPool).filter(SyntheticDataPool.pool_id == pool_id).first()
        if not pool:
            raise HTTPException(status_code=404, detail=f"Pool {pool_id} not found")

        return {
            "pool_id": pool.pool_id,
            "use_case": pool.use_case,
            "sdg_model_name": pool.sdg_model_name,
            "node_name": pool.node_name,
            "status": pool.status,
            "n_samples": pool.n_samples,
            "s3_uris": pool.s3_uris,
            "validation_reports": pool.validation_reports,
            "approval_reason": pool.approval_reason,
            "rejection_reason": pool.rejection_reason,
            "approved_by": pool.approved_by,
            "approved_at": pool.approved_at.isoformat() if pool.approved_at else None,
            "created_at": pool.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch pool {pool_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/synthetic-pools", tags=["synthetic-pools"])
async def list_synthetic_pools(
    status: Optional[str] = None,
    use_case: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication),
):
    """List synthetic data pools, optionally filtered by status and/or use_case.

    Used by the dashboard validation queue to fetch pools awaiting expert-committee
    approval (status="pending_approval").
    """
    from models import SyntheticDataPool

    try:
        query = session.query(SyntheticDataPool)
        if status:
            query = query.filter(SyntheticDataPool.status == status)
        if use_case:
            query = query.filter(SyntheticDataPool.use_case == use_case)
        pools = query.order_by(SyntheticDataPool.created_at.desc()).all()

        return {
            "pools": [
                {
                    "pool_id": pool.pool_id,
                    "use_case": pool.use_case,
                    "sdg_model_name": pool.sdg_model_name,
                    "node_name": pool.node_name,
                    "status": pool.status,
                    "n_samples": pool.n_samples,
                    "s3_uris": pool.s3_uris,
                    "validation_reports": pool.validation_reports,
                    "approval_reason": pool.approval_reason,
                    "rejection_reason": pool.rejection_reason,
                    "approved_by": pool.approved_by,
                    "approved_at": pool.approved_at.isoformat() if pool.approved_at else None,
                    "created_at": pool.created_at.isoformat()
                }
                for pool in pools
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list synthetic pools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthetic-pools/{pool_id}/approve", tags=["synthetic-pools"])
async def approve_synthetic_pool(pool_id: str, approved_by: str = "system", session: Session = Depends(get_session), current_user: UserClaims = Depends(require_authentication)):
    """Approve a synthetic data pool for publication."""
    from models import SyntheticDataPool
    from datetime import datetime

    try:
        pool = session.query(SyntheticDataPool).filter(SyntheticDataPool.pool_id == pool_id).first()
        if not pool:
            raise HTTPException(status_code=404, detail=f"Pool {pool_id} not found")

        if pool.status != "pending_approval":
            raise HTTPException(status_code=400, detail=f"Pool status is {pool.status}, cannot approve")

        pool.status = "approved"
        pool.approved_by = approved_by
        pool.approved_at = datetime.utcnow()
        pool.updated_at = datetime.utcnow()

        session.add(pool)
        session.commit()

        logger.info(f"Pool {pool_id} approved by {approved_by}")

        return {
            "pool_id": pool.pool_id,
            "status": pool.status,
            "approved_by": pool.approved_by,
            "approved_at": pool.approved_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve pool {pool_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthetic-pools/{pool_id}/reject", tags=["synthetic-pools"])
async def reject_synthetic_pool(pool_id: str, rejected_by: str = "system", reason: str = "", session: Session = Depends(get_session), current_user: UserClaims = Depends(require_authentication)):
    """Reject a synthetic data pool."""
    from models import SyntheticDataPool
    from datetime import datetime

    try:
        pool = session.query(SyntheticDataPool).filter(SyntheticDataPool.pool_id == pool_id).first()
        if not pool:
            raise HTTPException(status_code=404, detail=f"Pool {pool_id} not found")

        if pool.status != "pending_approval":
            raise HTTPException(status_code=400, detail=f"Pool status is {pool.status}, cannot reject")

        pool.status = "rejected"
        pool.rejected_by = rejected_by
        pool.rejection_reason = reason
        pool.rejected_at = datetime.utcnow()
        pool.updated_at = datetime.utcnow()

        session.add(pool)
        session.commit()

        logger.info(f"Pool {pool_id} rejected by {rejected_by}. Reason: {reason}")

        return {
            "pool_id": pool.pool_id,
            "status": pool.status,
            "rejected_by": pool.rejected_by,
            "rejection_reason": pool.rejection_reason,
            "rejected_at": pool.rejected_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject pool {pool_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Node Capability Endpoints ============

@app.post("/nodes", tags=["nodes"])
async def register_or_update_node(
    node_name: str,
    cpu_cores: Optional[int] = None,
    memory_gb: Optional[float] = None,
    storage_gb: Optional[float] = None,
    score: Optional[float] = None,
    capacity: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Register or update node capability information."""
    from models import NodeInfo

    try:
        node = session.query(NodeInfo).filter(NodeInfo.node_name == node_name).first()
        if not node:
            node = NodeInfo(node_name=node_name)

        if cpu_cores is not None:
            node.cpu_cores = cpu_cores
        if memory_gb is not None:
            node.memory_gb = memory_gb
        if storage_gb is not None:
            node.storage_gb = storage_gb
        if score is not None:
            node.score = score
        if capacity is not None:
            node.capacity = capacity

        node.updated_at = datetime.utcnow()
        session.add(node)
        session.commit()
        session.refresh(node)

        logger.info(f"Registered/updated node {node_name}")

        return {
            "node_name": node.node_name,
            "cpu_cores": node.cpu_cores,
            "memory_gb": node.memory_gb,
            "storage_gb": node.storage_gb,
            "score": node.score,
            "capacity": node.capacity,
            "status": node.status,
            "updated_at": node.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to register node {node_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/nodes/{node_name}", tags=["nodes"])
async def get_node_info(node_name: str, session: Session = Depends(get_session)):
    """Retrieve node capability information."""
    from models import NodeInfo

    try:
        node = session.query(NodeInfo).filter(NodeInfo.node_name == node_name).first()
        if not node:
            return {"node_name": node_name, "cpu_cores": None, "memory_gb": None, "storage_gb": None, "score": None, "capacity": None, "status": "unknown"}

        return {
            "node_name": node.node_name,
            "cpu_cores": node.cpu_cores,
            "memory_gb": node.memory_gb,
            "storage_gb": node.storage_gb,
            "score": node.score,
            "capacity": node.capacity,
            "status": node.status
        }
    except Exception as e:
        logger.error(f"Failed to fetch node {node_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ============ Synthetic Pool Upload (MinIO) ============
import io as _io
import os as _os
from fastapi import UploadFile, File, Form
from minio import Minio
from minio.error import S3Error


def _get_minio_client() -> Minio:
    endpoint = _os.getenv("MINIO_ENDPOINT", "minio:9000")
    endpoint = endpoint.replace("http://", "").replace("https://", "")
    return Minio(
        endpoint=endpoint,
        access_key=_os.getenv("MINIO_ACCESS_KEY", "admin"),
        secret_key=_os.getenv("MINIO_SECRET_KEY", "adminpassword"),
        secure=_os.getenv("MINIO_SECURE", "false").lower() == "true",
    )


@app.post("/synthetic-pools/upload", tags=["synthetic-pools"])
async def upload_synthetic_pool_to_minio(
    file: UploadFile = File(...),
    experiment_id: str = Form(...),
    report_type: Optional[str] = Form(None),
    node_id: Optional[str] = Form(None),
    current_user: UserClaims = Depends(require_authentication),
):
    """Upload a synthetic data pool (or validation report) to the MinIO data plane.

    Object layout matches the FL server's direct uploads so both paths are interchangeable:
      * pool   -> models/{experiment_id}/synthetic_big_pool.csv
      * report -> models/{experiment_id}/reports/node_{node_id}_{report_type}.html

    Pass ``report_type`` (e.g. "utility"/"privacy") for an HTML report; omit it for a CSV pool.
    Returns the bucket, object name and an ``s3://`` URI.
    """
    bucket = _os.getenv("MINIO_BUCKET", "synthema-catalogue")
    data = await file.read()

    if report_type:
        object_name = f"models/{experiment_id}/reports/node_{node_id or 'agg'}_{report_type}.html"
        content_type = "text/html"
    else:
        object_name = f"models/{experiment_id}/synthetic_big_pool.csv"
        content_type = "text/csv"

    try:
        client = _get_minio_client()
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=_io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        logger.info(f"Uploaded {object_name} to MinIO bucket {bucket}")
        return {
            "bucket": bucket,
            "object_name": object_name,
            "uri": f"s3://{bucket}/{object_name}",
            "size": len(data),
        }
    except S3Error as e:
        logger.error(f"MinIO upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"MinIO upload failed: {e}")


@app.get("/synthetic-pools/{pool_id}/reports/{report_key}", tags=["synthetic-pools"])
async def get_synthetic_pool_report(
    pool_id: str, report_key: str, session: Session = Depends(get_session),
    current_user: UserClaims = Depends(require_authentication),
):
    """Stream a pool's validation report HTML from MinIO (browser-openable).

    Resolves ``report_key`` against the pool's own ``validation_reports`` map, so
    only objects the pool references can be fetched (no arbitrary object access).
    This lets the dashboard render reports without exposing MinIO to the browser.
    """
    from models import SyntheticDataPool

    pool = session.query(SyntheticDataPool).filter(
        SyntheticDataPool.pool_id == pool_id
    ).first()
    if not pool:
        raise HTTPException(status_code=404, detail=f"Pool {pool_id} not found")

    reports = pool.validation_reports or {}
    uri = reports.get(report_key)
    if not uri:
        raise HTTPException(
            status_code=404, detail=f"Report '{report_key}' not found for pool {pool_id}"
        )

    # Parse "s3://bucket/object" or "bucket/object" into bucket + object key.
    raw = uri.split("://", 1)[-1]
    parts = raw.split("/", 1)
    if len(parts) != 2 or not parts[1]:
        raise HTTPException(status_code=400, detail="Malformed report URI in pool record")
    bucket, object_name = parts[0], parts[1]

    try:
        client = _get_minio_client()
        obj = client.get_object(bucket, object_name)
        content = obj.read()
        obj.close()
        obj.release_conn()
    except S3Error as e:
        raise HTTPException(status_code=404, detail=f"Report object unavailable: {e}")

    return Response(content=content, media_type="text/html")


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    from config import settings
    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)




























































