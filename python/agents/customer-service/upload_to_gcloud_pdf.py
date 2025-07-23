import os
import psycopg2
from dotenv import load_dotenv
from google.cloud import storage
import logging

# Configure logging to write to a file
logging.basicConfig(filename='index.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
load_dotenv(".env.db")

# --- Environment and GCloud Configuration ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")
BUCKET_NAME = os.environ.get("GOOGLE_GCS_BUCKET_NAME") # e.g., 'your-rag-bucket'

# --- Database Functions ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg2.connect(
        dbname=os.environ.get("GOOGLE_DB_NAME"),
        user=os.environ.get("GOOGLE_DB_USER"),
        password=os.environ.get("GOOGLE_DB_PASSWORD"),
        host=os.environ.get("GOOGLE_DB_HOST"),
        port=os.environ.get("GOOGLE_DB_PORT"),
    )

def get_unindexed_part_numbers(download_folder="customer_service/data/datasheets/pending/"):
    """Fetches part numbers whose datasheets exist locally but haven't been uploaded yet."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT "Nro. de Parte" FROM productos WHERE datasheet_indexed_at IS NULL;')
    part_numbers_to_check = [row[0] for row in cur.fetchall() if row[0] and row[0].strip()]
    
    unindexed_pns = []
    for pn in part_numbers_to_check:
        sanitized_filename = "".join(c for c in pn if c.isalnum() or c in ('-', '_')).rstrip()
        file_path = os.path.join(download_folder, f"{sanitized_filename}.pdf")
        if os.path.exists(file_path):
            unindexed_pns.append(pn)
            
    cur.close()
    conn.close()
    return unindexed_pns

def update_indexed_status(part_number):
    """Updates the datasheet_indexed_at column for a given part number."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE productos SET datasheet_indexed_at = NOW() WHERE "Nro. de Parte" = %s;', (part_number,))
    conn.commit()
    cur.close()
    conn.close()

# --- Google Cloud Storage Functions ---
def upload_to_gcs(local_file_path, destination_blob_name):
    """Uploads a file to the GCS bucket."""
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(local_file_path)
        logging.info(f"Successfully uploaded {local_file_path} to gs://{BUCKET_NAME}/{destination_blob_name}")
        return True
    except Exception as e:
        logging.error(f"Failed to upload {local_file_path} to GCS. Reason: {e}")
        return False

# --- Main Execution ---
if __name__ == "__main__":
    if not all([PROJECT_ID, LOCATION, BUCKET_NAME]):
        logging.error("Error: GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, or GOOGLE_GCS_BUCKET_NAME not set.")
        exit(1)

    logging.info("Starting datasheet upload process for RAG...")
    part_numbers_to_upload = get_unindexed_part_numbers()

    if not part_numbers_to_upload:
        logging.info("No new datasheets found to upload.")
    else:
        logging.info(f"Found {len(part_numbers_to_upload)} datasheets to upload.")
        successful_uploads = 0
        for i, pn in enumerate(part_numbers_to_upload):
            logging.info(f"--- Processing datasheet {i+1}/{len(part_numbers_to_upload)} for {pn} ---")
            sanitized_filename = "".join(c for c in pn if c.isalnum() or c in ('-', '_')).rstrip()
            local_path = os.path.join("customer_service", "data", "datasheets", "pending", f"{sanitized_filename}.pdf")
            
            # The destination path in GCS will be the filename itself
            gcs_destination_path = f"datasheets/{sanitized_filename}.pdf"

            if upload_to_gcs(local_path, gcs_destination_path):
                update_indexed_status(pn)
                successful_uploads += 1
                logging.info(f"Successfully processed and updated status for {pn}.")
            else:
                logging.warning(f"Failed to process {pn}. Status not updated.")

        logging.info(f"Upload process finished. Successfully uploaded {successful_uploads}/{len(part_numbers_to_upload)} files.")

    logging.info("Datasheet upload process finished.")
