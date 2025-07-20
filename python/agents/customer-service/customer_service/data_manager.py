import pandas as pd
from typing import List, Dict, Any

# Variable global para almacenar en caché los productos una vez que se han cargado.
# Esto evita leer el archivo CSV repetidamente, mejorando el rendimiento.
_products_cache = None

def load_products_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Carga los productos desde un archivo CSV en una lista de diccionarios.

    Esta función lee un archivo CSV, realiza la limpieza y conversión de tipos
    de datos en las columnas numéricas, y almacena los productos en una caché
    en memoria para accesos futuros más rápidos.

    Args:
        file_path (str): La ruta completa al archivo CSV.

    Returns:
        List[Dict[str, Any]]: Una lista de diccionarios, donde cada diccionario
                                representa un producto con sus atributos.
                                Retorna una lista vacía si el archivo no se encuentra.
    """
    global _products_cache
    # Verifica si los productos ya están en la caché.
    # Si la caché no está vacía, devuelve los datos ya cargados.
    if _products_cache is not None:
        return _products_cache

    try:
        # Lee el archivo CSV completo utilizando la librería pandas.
        # 'df' (DataFrame) es una estructura de datos tabular que representa el CSV.
        df = pd.read_csv(file_path, sep=';', encoding='latin1')

        # --- Limpieza y Conversión de Columnas Numéricas ---
        # Las siguientes líneas procesan columnas específicas para:
        # 1. Eliminar comas (',') que podrían usarse como separadores de miles en algunos formatos.
        #    Esto asegura que los valores sean interpretados correctamente como números.
        # 2. Convertir la columna al tipo de dato numérico apropiado (float para decimales, int para enteros).

        # Columna "Precio sin IVA": Elimina comas y convierte a número flotante.
        df["Precio sin IVA"] = df["Precio sin IVA"].replace({',': ''}, regex=True).astype(float)
        # Columna "(%)IVA": Elimina comas y convierte a número flotante.
        df["%IVA"] = df["%IVA"].replace({',': ''}, regex=True).astype(float)
        # Columna "Imp. Int.": Elimina comas y convierte a número flotante.
        df["Imp. Int."] = df["Imp. Int."].replace({',': ''}, regex=True).astype(float)
        # Columna "Precio Final U$D": Elimina comas y convierte a número flotante.
        df["Precio Final U$D"] = df["Precio Final U$D"].replace({',': ''}, regex=True).astype(float)
        
        # Columna "Stock":
        # - pd.to_numeric: Intenta convertir a número.
        # - errors='coerce': Si hay un valor que no se puede convertir, lo convierte a NaN (Not a Number).
        # - fillna(0): Rellena los valores NaN (los que no se pudieron convertir) con 0.
        # - astype(int): Finalmente, convierte toda la columna a número entero.
        df["Stock"] = pd.to_numeric(df["Stock"], errors='coerce').fillna(0).astype(int)

        # --- Almacenamiento en Caché ---
        # Convierte el DataFrame de pandas a una lista de diccionarios.
        # Cada diccionario en la lista representa una fila del CSV (un producto),
        # donde las claves del diccionario son los nombres de las columnas del CSV.
        _products_cache = df.to_dict(orient='records')
        
        # Devuelve los datos cargados y procesados.
        return _products_cache
    
    except FileNotFoundError:
        # Si el archivo CSV no se encuentra en la ruta especificada,
        # registra el error (podría añadirse un log aquí) y devuelve una lista vacía
        # para indicar que no se pudieron cargar productos.
        print(f"Error: El archivo CSV no fue encontrado en la ruta: {file_path}")
        return []
    except Exception as e:
        # Captura cualquier otro error que pueda ocurrir durante la lectura o procesamiento del CSV.
        print(f"Ocurrió un error al cargar el CSV: {e}")
        return []