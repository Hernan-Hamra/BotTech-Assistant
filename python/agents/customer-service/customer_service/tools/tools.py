import logging
import os
from typing import List, Dict, Any, Optional
from customer_service.data_manager import search_products_from_db, get_product_by_code_from_db, _extract_socket_from_product_name
from customer_service.quote_manager import QuoteManager

logger = logging.getLogger(__name__)

# Instancia del gestor de presupuestos
quote_manager = QuoteManager()

# Load environment variables for Google Cloud Project and Location
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")
DATA_STORE_ID = "bottech_datasheets_rag" # Your RAG Datastore ID

def _normalize_stock_status(stock_value: int) -> str:
    """
    Normaliza el valor numérico del stock a un estado legible.
    """
    if stock_value == 0:
        return "Sin stock"
    elif 1 <= stock_value <= 3:
        return f"Stock bajo ({stock_value} unidades)"
    else:
        return f"En stock ({stock_value} unidades)"

def search_products(
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
    products = search_products_from_db(
        categoria=categoria,
        fabricante=fabricante,
        producto=producto,
        precio_max_usd=precio_max_usd,
        precio_min_usd=precio_min_usd,
        codigo=codigo,
        nro_de_parte=nro_de_parte,
        socket_type=socket_type # Pasar el nuevo parámetro
    )
    
    if not products:
        # Si no se encontraron productos con la búsqueda inicial, intentar una búsqueda más flexible
        # dentro de la misma categoría.
        flexible_products = []
        if producto: # Si se proporcionó un nombre de producto, buscarlo en nro_de_parte dentro de la categoría
            flexible_products = search_products_from_db(categoria=categoria, nro_de_parte=producto)
        elif nro_de_parte: # Si se proporcionó un nro_de_parte, buscarlo en producto dentro de la categoría
            flexible_products = search_products_from_db(categoria=categoria, producto=nro_de_parte)

        if flexible_products:
            # Tomar el primer producto como la sugerencia más parecida dentro de la categoría
            suggested_product = flexible_products[0]
            suggested_name = suggested_product.get("Producto", "")
            suggested_part_number = suggested_product.get("Nro. de Parte", "")
            return [{
                "message": f"No encontré una coincidencia exacta con el producto o número de parte que buscas. "
                           f"Pero el más parecido que encontré en la categoría {categoria} es: {suggested_name} (Nro. de Parte: {suggested_part_number}). "
                           f"¿Deseas consultar sobre este producto?"
            }]
        else:
            return []
    
    for product in products:
        if "Stock" in product:
            product["Stock"] = _normalize_stock_status(product["Stock"])
    
    return products

def query_datasheet_rag(query: str) -> List[str]:
    """
    Consulta el Datastore de Vertex AI Search (RAG) para obtener información
    relevante de los datasheets indexados.

    Args:
        query (str): La pregunta o término de búsqueda para el RAG.

    Returns:
        List[str]: Una lista de fragmentos de texto relevantes encontrados en los datasheets.
                   Retorna un mensaje si no se encuentra información.
    """
    if not PROJECT_ID or not LOCATION or not DATA_STORE_ID:
        logger.error("Google Cloud Project ID, Location, or Data Store ID not set for RAG query.")
        return ["Error: Configuración de RAG incompleta."]

    try:
        client = discoveryengine.SearchServiceClient()
        serving_config = client.serving_config_path(
            project=PROJECT_ID,
            location=LOCATION,
            data_store=DATA_STORE_ID,
            serving_config="default"
        )

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=5, # Limita el número de resultados para evitar respuestas muy largas
            query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
                mode=discoveryengine.SearchRequest.QueryExpansionSpec.Mode.AUTO
            ),
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippets=True
                )
            )
        )

        response = client.search(request)
        
        relevant_snippets = []
        for result in response.results:
            if result.snippet and result.snippet.snippet: # Asegura que el snippet no esté vacío
                relevant_snippets.append(result.snippet.snippet)
            elif result.document and result.document.derived_struct_data and 'extractive_answers' in result.document.derived_struct_data:
                # Fallback for extractive answers if direct snippets are not ideal
                for answer in result.document.derived_struct_data['extractive_answers']:
                    if 'content' in answer:
                        relevant_snippets.append(answer['content'])

        if relevant_snippets:
            return relevant_snippets
        else:
            return ["No se encontró información relevante en los datasheets para su consulta."]

    except Exception as e:
        logger.error(f"Error al consultar el RAG: {e}")
        return [f"Error al consultar la base de datos de datasheets: {e}"]

# --- Herramientas para la Gestión de Presupuestos ---

def add_item_to_quote(product_code: str, quantity: int = 1) -> Dict[str, Any]:
    """Añade un producto al presupuesto por su código y la cantidad deseada. Devuelve el presupuesto actualizado."""
    product = get_product_by_code_from_db(product_code)
    if not product:
        return {"error": f"Producto con código {product_code} no encontrado."}
    
    quote_manager.add_item(product, quantity)
    return quote_manager.get_quote()

def view_quote() -> Dict[str, Any]:
    """Muestra el contenido actual del presupuesto, incluyendo los productos, cantidades y el total."""
    return quote_manager.get_quote()

def remove_item_from_quote(product_code: str) -> Dict[str, Any]:
    """Elimina un producto del presupuesto por su código. Devuelve el presupuesto actualizado."""
    quote_manager.remove_item(product_code)
    return quote_manager.get_quote()

def clear_quote() -> Dict[str, Any]:
    """Vacía completamente el presupuesto actual."""
    quote_manager.clear_quote()
    return quote_manager.get_quote()
