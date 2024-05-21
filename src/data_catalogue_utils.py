import sqlite3
from fastapi import HTTPException
from pydantic import BaseModel
import os

DATABASE_FILE = "/mnt/c/users/lenovo/desktop/fastapi/SYNTHEMA/central_node.db"
#DATABASE_FILE = "./central_node.db"

class NodeDatasetInfo(BaseModel):
    node: str
    path: str
    disease: str
    #nrows: int
    #ncols: int
    #provider: str
    #iid: str

###########################################
# CONNECTION BETWEEN FASTAPI AND SQLITE #
###########################################

# Funzione per creare la connessione al database SQLite
#def create_connection():
#    conn = None
#    try:
#        conn = sqlite3.connect(DATABASE_FILE)
#        print(f"Connected to SQLite database '{DATABASE_FILE}'")
#        return conn
#    except Exception as e:
#        print(e)

def create_connection():
    try:
        if not os.path.exists(DATABASE_FILE):
            print(f"Database file {DATABASE_FILE} does not exist.")

        conn = sqlite3.connect(DATABASE_FILE)
        print(f"Connected to SQLite database '{DATABASE_FILE}'")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

######################
# DATASET MANAGEMENT #
######################

# Save dataset info (disease, node, path) into the database
def save_dataset_info_to_database(node_dataset: NodeDatasetInfo):
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

    except Exception as e:
        print("Error saving dataset info to database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Retrieve dataset info from node and disease
def get_dataset_info_from_database(node: str, disease: str):
    try:
        # Connect to the database
        conn = create_connection()
        cursor = conn.cursor()

        # Execute the SQL query to retrieve dataset information
        cursor.execute("""
            SELECT node, path, disease
            FROM datasets
            WHERE node = ? AND disease = ?
        """, (node, disease))

        # Fetch the result
        dataset_info = cursor.fetchone()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return dataset_info

    except Exception as e:
        print("Error retrieving dataset info from database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Remove the dataset info from the database
def remove_dataset_info_from_database(node: str, disease: str, path:str)->bool:
    try:
        # Connect to the database
        conn = create_connection()
        cursor = conn.cursor()

        # Esegui una query di selezione per verificare se il record esiste
        cursor.execute("""
                    SELECT * FROM datasets
                    WHERE node = ? AND disease = ? AND path = ?
                """, (node, disease, path))

        record = cursor.fetchone()
        if record is None:
            return False

        # Delete the dataset entry from the database
        cursor.execute("""
            DELETE FROM datasets
            WHERE node = ? AND disease = ? AND path = ?
        """, (node, disease, path))

        rowcount = cursor.rowcount
        # Commit the transaction and close the connection
        conn.commit()
        cursor.close()
        conn.close()

        return rowcount > 0

    except Exception as e:
        print("Error removing dataset info from database:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def fetch_all_datasets():
    # Function to fetch all datasets and their metadata from SQLite database
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT node, path, disease FROM datasets")
    rows = cursor.fetchall()
    conn.close()

    datasets = []
    for row in rows:
        dataset = {
            "node": row[0],
            "path": row[1],#json.loads(row[1]),  # Convert JSON string back to dictionary
            "disease": row[2]
        }
        datasets.append(dataset)

    return datasets
