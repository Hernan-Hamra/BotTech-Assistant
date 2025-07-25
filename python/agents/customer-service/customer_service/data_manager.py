import logging
from typing import List, Dict, Any, Optional
import os
import psycopg2
from psycopg2.extras import DictCursor
from .config import Config # Importa la clase Config desde el módulo de configuración local.
from decimal import Decimal
import re

configs = Config() # Instancia la clase Config para cargar la configuración del agente.

# --- Database Connection ---

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=configs.DB_NAME,
            user=configs.DB_USER,
            password=configs.DB_PASSWORD,
            host=configs.DB_HOST,
            port=configs.DB_PORT
        )
        # Asegurarse de que la extensión pg_trgm esté habilitada
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        conn.commit()
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def _convert_decimals_to_floats(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte todos los objetos Decimal en un diccionario a float."""
    for key, value in data.items():
        if isinstance(value, Decimal):
            data[key] = float(value)
    return data

def _extract_socket_from_product_name(product_name: str) -> Optional[str]:
    """
    Extrae el tipo de socket de una cadena de nombre de producto.
    Ejemplos: "S1200", "AM4", "AM5", "LGA1700", "1700", "1200", "1151", "1150", "2066", "TR4", "sTRX4"
    """
    # Patrones de sockets comunes
    patterns = [
        r'S(\d{3,4})',  # S1200, S1700
        r'AM(\d)',     # AM4, AM5
        r'LGA(\d{3,4})', # LGA1700, LGA1200
        r'(\d{3,4})',   # 1700, 1200 (números de 3 o 4 dígitos)
        r'TR(\d)',     # TR4
        r'sTRX(\d)'    # sTRX4
    ]

    for pattern in patterns:
        match = re.search(pattern, product_name, re.IGNORECASE)
        if match:
            return match.group(0).upper() # Devuelve la coincidencia completa en mayúsculas
    return None

def get_product_by_code_from_db(code: str) -> Optional[Dict[str, Any]]:
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
    
    return _convert_decimals_to_floats(dict(product)) if product else None



def search_products_from_db(
    categoria: Optional[str] = None,
    fabricante: Optional[str] = None,
    producto: Optional[str] = None,
    precio_max_usd: Optional[float] = None,
    precio_min_usd: Optional[float] = None,
    codigo: Optional[str] = None,
    nro_de_parte: Optional[str] = None,
    socket_type: Optional[str] = None, # Nuevo parámetro para filtrar por socket
) -> List[Dict[str, Any]]:
    """
    Busca productos en la base de datos basándose en los criterios proporcionados.
    Implementa una estrategia de búsqueda por niveles para mayor robustez.
    """
    conn = get_db_connection()
    if conn is None:
        return []

    products = []
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Nivel 1: Búsqueda por Código o Número de Parte (Exacta)
            if codigo or nro_de_parte:
                query = "SELECT * FROM productos WHERE 1=1"
                params = []
                if codigo:
                    query += " AND \"Codigo\" = %s"
                    params.append(codigo)
                if nro_de_parte:
                    normalized_nro_de_parte = nro_de_parte.replace(" ", "")
                    query += " AND REPLACE(\"Nro. de Parte\", ' ', '') ILIKE %s"
                    params.append(f"%{normalized_nro_de_parte}%")
                cur.execute(query, params)
                products = [_convert_decimals_to_floats(dict(row)) for row in cur.fetchall()]
                if products: return products

            # Nivel 2: Búsqueda por Categoría y Producto/Fabricante (Similitud y ILIKE para series)
            if categoria or producto or fabricante or socket_type:
                query = "SELECT * FROM productos WHERE 1=1"
                params = []
                order_clauses = []

                if categoria:
                    query += " AND similarity(\"Categoria\", %s) > 0.2"
                    params.append(categoria)
                    order_clauses.append("similarity(\"Categoria\", %s) DESC")
                    params.append(categoria)
                
                if producto:
                    # Check for common processor series abbreviations
                    processed_producto = producto.lower()
                    search_terms = []

                    if processed_producto == 'r3':
                        search_terms = ['ryzen 3', 'r3']
                    elif processed_producto == 'r5':
                        search_terms = ['ryzen 5', 'r5']
                    elif processed_producto == 'r7':
                        search_terms = ['ryzen 7', 'r7']
                    elif processed_producto == 'r9':
                        search_terms = ['ryzen 9', 'r9']
                    elif processed_producto == 'i3':
                        search_terms = ['core i3', 'i3']
                    elif processed_producto == 'i5':
                        search_terms = ['core i5', 'i5']
                    elif processed_producto == 'i7':
                        search_terms = ['core i7', 'i7']
                    elif processed_producto == 'i9':
                        search_terms = ['core i9', 'i9']
                    else:
                        search_terms = [producto] # Default to original product term

                    # Build the product search condition
                    product_conditions = []
                    product_params = []
                    for term in search_terms:
                        product_conditions.append("(\"Producto\" ILIKE %s OR similarity(\"Producto\", %s) > 0.1)")
                        product_params.append(f"%{term}%")
                        product_params.append(term) # For similarity

                    query += " AND (" + " OR ".join(product_conditions) + ")"
                    params.extend(product_params)

                    order_clauses.append("similarity(\"Producto\", %s) DESC")
                    params.append(producto) # Still order by original product term similarity
                
                if fabricante:
                    query += " AND \"Fabricante\" ILIKE %s"
                    params.append(f"%{fabricante}%")
                
                if socket_type: # Nuevo filtro por socket
                    socket_patterns = [
                        f"%{socket_type}%",
                        f"%S{socket_type}%",
                        f"%LGA{socket_type}%"
                    ]
                    socket_conditions = []
                    for pattern in socket_patterns:
                        socket_conditions.append("\"Producto\" ILIKE %s")
                        params.append(pattern)
                    query += " AND (" + " OR ".join(socket_conditions) + ")"
                
                if precio_max_usd is not None:
                    query += " AND \"Precio Final U$D\" <= %s"
                    params.append(precio_max_usd)
                if precio_min_usd is not None:
                    query += " AND \"Precio Final U$D\" >= %s"
                    params.append(precio_min_usd)

                order_clauses.append("\"Stock\" DESC")
                order_clauses.append("id ASC")
                query += " ORDER BY " + ", ".join(order_clauses)
                query += " LIMIT 10"

                cur.execute(query, params)
                products = [_convert_decimals_to_floats(dict(row)) for row in cur.fetchall()]
                if products: return products

            # Nivel 3: Búsqueda Amplia por Producto (Similitud, si solo se dio producto)
            if producto:
                query = "SELECT * FROM productos WHERE similarity(\"Producto\", %s) > 0.05"
                params = [producto]
                order_clauses = ["similarity(\"Producto\", %s) DESC", "\"Stock\" DESC", "id ASC"]
                params.append(producto)
                query += " ORDER BY " + ", ".join(order_clauses)
                query += " LIMIT 10"
                cur.execute(query, params)
                products = [_convert_decimals_to_floats(dict(row)) for row in cur.fetchall()]
                if products: return products

    except Exception as e:
        print(f"Error al buscar productos en la base de datos: {e}")
    finally:
        conn.close()

    return products
