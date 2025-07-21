import logging
from typing import List, Dict, Any, Optional
from customer_service.data_manager import search_products_from_db # Importa la función para buscar productos en la base de datos

# Configuración del logger para este módulo.
# Esto permite registrar mensajes (información, advertencias, errores)
# que pueden ser útiles para depurar o monitorear el comportamiento del bot.
logger = logging.getLogger(__name__)

def search_products_csv(
    categoria: Optional[str] = None, # Parámetro opcional: categoría del producto (ej. "Notebook", "Monitor")
    fabricante: Optional[str] = None, # Parámetro opcional: fabricante del producto (ej. "HP", "Samsung")
    producto: Optional[str] = None, # Parámetro opcional: término de búsqueda en el nombre del producto
    precio_max_usd: Optional[float] = None, # Parámetro opcional: precio máximo en USD
    precio_min_usd: Optional[float] = None, # Parámetro opcional: precio mínimo en USD
    codigo: Optional[str] = None, # Parámetro opcional: código del producto
) -> List[Dict[str, Any]]:
    """
    Busca productos en la base de datos basándose en los criterios proporcionados.

    Esta función delega la búsqueda a la base de datos, utilizando los parámetros
    para construir una consulta SQL.

    Args:
        categoria (Optional[str]): La categoría del producto a buscar.
        fabricante (Optional[str]): El fabricante del producto a buscar.
        producto (Optional[str]): Un término de búsqueda para encontrar en el nombre del producto.
                                  Permite búsquedas parciales.
        precio_max_usd (Optional[float]): El precio máximo permitido para el producto en USD.
        precio_min_usd (Optional[float]): El precio mínimo permitido para el producto en USD.
        codigo (Optional[str]): El código de producto a buscar.

    Returns:
        List[Dict[str, Any]]: Una lista de diccionarios, donde cada diccionario representa
                              un producto que coincide con los criterios de búsqueda.
                              Retorna un mensaje si no se encuentran productos.
    """
    # Llama a la función de búsqueda en la base de datos con todos los parámetros.
    products = search_products_from_db(
        categoria=categoria,
        fabricante=fabricante,
        producto=producto,
        precio_max_usd=precio_max_usd,
        precio_min_usd=precio_min_usd,
        codigo=codigo
    )
    
    if not products:
        return [{"message": "No se encontraron productos que coincidan con los criterios de búsqueda."}]
    
    return products