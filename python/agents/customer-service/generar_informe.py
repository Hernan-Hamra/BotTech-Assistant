import os
import psycopg2
from dotenv import load_dotenv

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

def get_all_part_numbers():
    """Fetches all part numbers from the productos table."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT "Nro. de Parte" FROM productos;')
    part_numbers = [row[0] for row in cur.fetchall() if row[0] and row[0].strip()]
    cur.close()
    conn.close()
    return part_numbers

def generate_report(part_numbers, download_folder="customer_service/data/datasheets/"):
    """Generates a report of downloaded and missing datasheets."""
    downloaded_files = os.listdir(download_folder)
    # We remove the .pdf extension to compare with the part number
    downloaded_pns = {os.path.splitext(f)[0] for f in downloaded_files}

    with_pdf = []
    without_pdf = []

    for pn in part_numbers:
        sanitized_pn = "".join(c for c in pn if c.isalnum() or c in ('-', '_')).rstrip()
        if sanitized_pn in downloaded_pns:
            with_pdf.append(pn)
        else:
            without_pdf.append(pn)

    report_content = f"""
    # Informe de Descarga de Datasheets

    Total de Artículos Únicos: {len(part_numbers)}
    Artículos con PDF Descargado: {len(with_pdf)}
    Artículos sin PDF: {len(without_pdf)}

    --- Artículos CON PDF ({len(with_pdf)}) ---
    """
    report_content += "\n".join(with_pdf)
    report_content += f"""

    --- Artículos SIN PDF ({len(without_pdf)}) ---
    """
    report_content += "\n".join(without_pdf)

    with open("informe_descargas.txt", "w") as f:
        f.write(report_content)
    print("Informe generado exitosamente en 'informe_descargas.txt'")

if __name__ == "__main__":
    all_pns = get_all_part_numbers()
    generate_report(all_pns)
