import os
import time
import psycopg2
import requests
import logging
from dotenv import load_dotenv
from serpapi import GoogleSearch

# Configure logging
logging.basicConfig(filename='download.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    load_dotenv(".env.db")
    conn = psycopg2.connect(
        dbname=os.environ.get("GOOGLE_DB_NAME"),
        user=os.environ.get("GOOGLE_DB_USER"),
        password=os.environ.get("GOOGLE_DB_PASSWORD"),
        host=os.environ.get("GOOGLE_DB_HOST"),
        port=os.environ.get("GOOGLE_DB_PORT"),
    )
    return conn

def get_unique_part_numbers():
    """Fetches unique part numbers from the productos table."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT "Nro. de Parte" FROM productos;')
    part_numbers = [row[0] for row in cur.fetchall() if row[0] and row[0].strip()]
    cur.close()
    conn.close()
    return part_numbers

def download_datasheet(part_number, api_key, download_folder="customer_service/data/datasheets/"):
    """
    Searches for a PDF datasheet using SerpApi and downloads it.
    """
    params = {
        "api_key": api_key,
        "engine": "google",
        "q": f'{part_number} datasheet filetype:pdf',
        "hl": "en",
    }

    logging.info(f"Searching for: {params['q']}")

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        pdf_url_found = None
        if 'organic_results' in results:
            for result in results['organic_results']:
                if 'link' in result and result['link'].lower().endswith('.pdf'):
                    pdf_url_found = result['link']
                    break

        if pdf_url_found:
            logging.info(f"Found PDF datasheet for {part_number} at: {pdf_url_found}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            pdf_response = requests.get(pdf_url_found, headers=headers, timeout=60)
            pdf_response.raise_for_status()

            sanitized_filename = "".join(c for c in part_number if c.isalnum() or c in ('-', '_')).rstrip()
            file_path = os.path.join(download_folder, f"{sanitized_filename}.pdf")

            with open(file_path, 'wb') as f:
                f.write(pdf_response.content)
            logging.info(f"Successfully downloaded and saved to {file_path}")
            return True
        else:
            logging.warning(f"No direct PDF link found for {part_number} in the search results.")
            return False

    except Exception as e:
        logging.error(f"An error occurred while processing {part_number}: {e}")
        return False

if __name__ == "__main__":
    load_dotenv()
    serpapi_key = os.environ.get("GOOGLE_SERPAPI_API_KEY")

    if not serpapi_key:
        logging.error("Error: SERPAPI_API_KEY not found in .env file.")
    else:
        part_numbers = get_unique_part_numbers()
        
        if part_numbers:
            logging.info(f"Found {len(part_numbers)} unique part numbers to process.")
            download_folder = "customer_service/data/datasheets/"
            os.makedirs(download_folder, exist_ok=True)
            
            processed_count = 0
            for i, pn in enumerate(part_numbers):
                if processed_count >= 90:
                    logging.info("Reached 90 requests, pausing for an hour.")
                    print("Reached 90 requests, pausing for an hour.")
                    time.sleep(3600)
                    processed_count = 0

                sanitized_filename = "".join(c for c in pn if c.isalnum() or c in ('-', '_')).rstrip()
                file_path = os.path.join(download_folder, f"{sanitized_filename}.pdf")

                if os.path.exists(file_path):
                    logging.info(f"Datasheet for {pn} already exists. Skipping.")
                    continue
                
                logging.info(f"--- Processing part number {i+1}/{len(part_numbers)}: {pn} ---")
                if download_datasheet(pn, serpapi_key, download_folder):
                    processed_count += 1
                
                # Optional: a small delay between requests to be safe
                time.sleep(2)
        else:
            logging.info("No part numbers found in the database.")