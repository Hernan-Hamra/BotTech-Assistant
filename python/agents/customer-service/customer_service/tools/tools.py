import logging
from typing import List, Dict, Any, Optional
from customer_service.data_manager import load_products_from_csv # Importa la función para cargar productos desde el CSV

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
) -> List[Dict[str, Any]]:
    """
    Busca productos en el catálogo CSV basándose en los criterios proporcionados.

    Esta función filtra la lista completa de productos cargada desde el CSV
    según la categoría, fabricante, nombre del producto y rangos de precio.
    Prioriza los productos con stock y limita el número de resultados.

    Args:
        categoria (Optional[str]): La categoría del producto a buscar.
        fabricante (Optional[str]): El fabricante del producto a buscar.
        producto (Optional[str]): Un término de búsqueda para encontrar en el nombre del producto.
                                  Permite búsquedas parciales.
        precio_max_usd (Optional[float]): El precio máximo permitido para el producto en USD.
        precio_min_usd (Optional[float]): El precio mínimo permitido para el producto en USD.

    Returns:
        List[Dict[str, Any]]: Una lista de diccionarios, donde cada diccionario representa
                              un producto que coincide con los criterios de búsqueda.
                              Retorna un mensaje si no se encuentran productos o si el catálogo está vacío.
    """
    # Carga todos los productos desde el archivo CSV usando la función del data_manager.
    # La ruta del archivo CSV es "data/Lista_de_Precios_Invid_24062025.csv".
    products = load_products_from_csv("customer_service/data/Lista_de_Precios_Invid_24062025.csv")
    
    # Verifica si la carga de productos no devolvió nada (ej. archivo no encontrado o vacío).
    if not products:
        # Retorna un diccionario con un mensaje indicando que no se encontraron productos.
        return [{"message": "No se encontraron productos en el catálogo para iniciar la búsqueda."}]

    # Inicializa la lista de productos filtrados con todos los productos cargados.
    # Esta lista se irá reduciendo a medida que se apliquen los filtros.
    filtered_products = products

    # --- Aplicación de Filtros ---

    # Filtro por Categoría:
    # Si se proporcionó una categoría, filtra los productos cuya categoría coincida.
    # Se convierte todo a minúsculas para hacer la búsqueda insensible a mayúsculas/minúsculas.
    # .get("Categoria") se usa para acceder a la clave de forma segura y evitar errores si la clave no existe.
    if categoria:
        filtered_products = [
            p for p in filtered_products if str(p.get("Categoria", "")).lower() == categoria.lower()
        ]

    # Filtro por Fabricante:
    # Si se proporcionó un fabricante, filtra los productos cuyo fabricante coincida.
    # Similar al filtro de categoría, se convierte a minúsculas.
    if fabricante:
        filtered_products = [
            p for p in filtered_products if str(p.get("Fabricante", "")).lower() == fabricante.lower()
        ]

    # Filtro por Nombre de Producto (búsqueda de subcadena):
    # Si se proporcionó un término de búsqueda de producto, filtra aquellos cuyo nombre de producto
    # contenga el término de búsqueda (insensible a mayúsculas/minúsculas).
    # Esto permite buscar, por ejemplo, "HP" dentro de "Laptop HP Spectre".
    if producto:
        filtered_products = [
            p for p in filtered_products if producto.lower() in str(p.get("Producto", "")).lower()
        ]

    # Filtro por Precio Máximo:
    # Si se proporcionó un precio máximo, filtra los productos cuyo 'Precio Final U$D' sea menor o igual.
    # Se usa .get("Precio Final U$D", 0) para manejar casos donde el precio no esté definido, asumiendo 0.
    if precio_max_usd:
        filtered_products = [
            p for p in filtered_products if p.get("Precio Final U$D", 0) <= precio_max_usd
        ]

    # Filtro por Precio Mínimo:
    # Si se proporcionó un precio mínimo, filtra los productos cuyo 'Precio Final U$D' sea mayor o igual.
    # Similar al precio máximo, se asume 0 si el precio no está definido.
    if precio_min_usd:
        filtered_products = [
            p for p in filtered_products if p.get("Precio Final U$D", 0) >= precio_min_usd
        ]

    # --- Priorización de Stock y Límite de Resultados ---

    # Divide los productos filtrados en dos listas: con stock y sin stock.
    # .get("Stock", 0) asegura que si la clave 'Stock' no existe, se considere 0.
    in_stock = [p for p in filtered_products if p.get("Stock", 0) > 0]
    out_of_stock = [p for p in filtered_products if p.get("Stock", 0) == 0]

    # Concatena las listas, colocando primero los productos con stock.
    # Luego, toma solo los primeros 10 productos de la lista combinada.
    # Esto garantiza que el bot ofrezca primero productos disponibles.
    return (in_stock + out_of_stock)[:10]