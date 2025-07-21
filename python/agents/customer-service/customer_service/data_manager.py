import logging
from typing import List, Dict, Any, Optional
import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv() # Carga las variables del archivo .env

# --- Database Connection ---

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def get_product_by_code_from_db(code: str) -> Dict[str, Any]:
    """Busca un producto por su código en la base de datos."""
    conn = get_db_connection()
    if conn is None:
        return None
    
    product = None
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute('SELECT * FROM productos WHERE "Codigo" = %s;', (code,))
            product = cur.fetchone()
    except Exception as e:
        print(f"Error al buscar el producto: {e}")
    finally:
        conn.close()
    
    return dict(product) if product else None

def search_products_from_db(
    categoria: Optional[str] = None,
    fabricante: Optional[str] = None,
    producto: Optional[str] = None,
    precio_max_usd: Optional[float] = None,
    precio_min_usd: Optional[float] = None,
    codigo: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Busca productos en la base de datos basándose en los criterios proporcionados.
    """
    conn = get_db_connection()
    if conn is None:
        return []

    products = []
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            query = "SELECT * FROM productos WHERE 1=1"
            params = []

            if categoria:
                query += " AND \"Categoria\" ILIKE %s"
                params.append(f"%{categoria}%")
            if fabricante:
                query += " AND \"Fabricante\" ILIKE %s"
                params.append(f"%{fabricante}%")
            if producto:
                query += " AND \"Producto\" ILIKE %s"
                params.append(f"%{producto}%")
            if codigo:
                query += " AND \"Codigo\" = %s"
                params.append(codigo)
            if precio_max_usd is not None:
                query += " AND \"Precio Final U$D\" <= %s"
                params.append(precio_max_usd)
            if precio_min_usd is not None:
                query += " AND \"Precio Final U$D\" >= %s"
                params.append(precio_min_usd)
            
            # Priorizar productos con stock y limitar a 10 resultados
            query += " ORDER BY \"Stock\" DESC, id ASC LIMIT 10"

            cur.execute(query, params)
            products = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error al buscar productos en la base de datos: {e}")
    finally:
        conn.close()

    return products