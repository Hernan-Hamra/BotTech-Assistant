

import sys
import os

# Añadir el directorio del proyecto al path para poder importar desde customer_service
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from customer_service.data_manager import get_product_by_code_from_db

def test_connection():
    print("--- Probando la conexión a la base de datos ---")
    # Usamos un código de producto que sabemos que existe
    test_code = '0416736'
    print(f"Buscando producto con código: {test_code}")
    
    product = get_product_by_code_from_db(test_code)
    
    if product:
        print("\n¡Éxito! Producto encontrado:")
        # Imprimir los detalles del producto de forma legible
        for key, value in product.items():
            print(f"  {key}: {value}")
    else:
        print("\nFallo. No se pudo encontrar el producto o hubo un error en la conexión.")


if __name__ == "__main__":
    test_connection()

