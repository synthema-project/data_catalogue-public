from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn
import logging
from data_catalogue_utils import NodeDatasetInfo, RemoveDatasetObject, save_dataset_info_to_database, get_dataset_info_from_database, remove_dataset_info_from_database, fetch_all_datasets, create_connection

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/metadata", tags=["data-catalogue"])
async def save_dataset_info_to_database(node_dataset: NodeDatasetInfo):
    try:
        # Connect to the database
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node TEXT NOT NULL,
                path TEXT NOT NULL,
                disease TEXT NOT NULL
            )
        """)
        # Insert dataset information into the database
        cursor.execute("""
            INSERT INTO datasets (node, path, disease)
            VALUES (?, ?, ?)
        """, (node_dataset.node, node_dataset.path, node_dataset.disease))#, node_dataset.nrows, node_dataset.ncols))

        # Commit the transaction and close the connection
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": 'Metadata uploaded successfully'}

    except Exception as e:
        print("Error saving dataset info to database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


# retrieve dataset info from database
@app.get("/metadata/{disease}", tags=["data-catalogue"])
async def retrieve_dataset_info(node: str, disease: str):
    try:
        # Retrieve dataset information from the database
        logger.info(f"Retrieving dataset info for node: {node}, disease: {disease}")
        dataset_info = get_dataset_info_from_database(node, disease)
        logger.info(f"Dataset info retrieved: {dataset_info}")

        if dataset_info is None:
            logger.warning(f"No dataset found for node: {node}, disease: {disease}")
            raise HTTPException(status_code=404, detail=f"No dataset found in the database for node: {node} and disease: {disease}")

        # Return the dataset information
        return {
            "node": dataset_info[0],
            "path": dataset_info[1],
            "disease": dataset_info[2],
            #"number of samples": dataset_info[3],
            #"number of features": dataset_info[4]
        }
    except HTTPException as e:
        # Re-raise the HTTPException to let FastAPI handle it properly
        raise e
    except Exception as e:
        logger.error(f"Error retrieving dataset info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving dataset info: {str(e)}")

@app.get("/metadata", tags=["data-catalogue"])
async def get_all_datasets():
    datasets = await fetch_all_datasets()
    if not datasets:
        raise HTTPException(status_code=404, detail="No datasets found")
    return {"datasets": datasets}

@app.delete("/metadata", tags=["data-catalogue"])
#async def delete_dataset(removedatasetobject: RemoveDatasetObject):#node: str, disease: str, path: str):
async def delete_dataset(node: str=Form(...), disease: str=Form(...), path: str=Form(...)):
    try:
        #result = remove_dataset_info_from_database(node=removedatasetobject.node, disease=removedatasetobject.disease, path=removedatasetobject.path)
        result = remove_dataset_info_from_database(node=node, disease=disease, path=path)
        if result:
            return {"message": f"Dataset '{path}' deleted successfully."}
        else:
            raise HTTPException(status_code=404, detail=f"Dataset '{path}' not found.")
    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get("/healthcheck")
async def healthcheck():
    #dummy health check
    #return Response(content="OK", status_code=200)
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=83)
