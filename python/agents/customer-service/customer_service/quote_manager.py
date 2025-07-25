from typing import List, Dict, Any, Optional

class QuoteManager:
    """
    Gestiona la creación y manipulación de un presupuesto o cotización.
    """
    def __init__(self):
        self.items: List[Dict[str, Any]] = []

    def add_item(self, product: Dict[str, Any], quantity: int):
        """Añade un producto al presupuesto."""
        # Verificar si el producto ya está en el presupuesto para actualizar la cantidad
        for item in self.items:
            if item['product']['Codigo'] == product['Codigo']:
                item['quantity'] += quantity
                return

        self.items.append({'product': product, 'quantity': quantity})

    def remove_item(self, product_code: str):
        """Elimina un producto del presupuesto por su código."""
        self.items = [item for item in self.items if item['product']['Codigo'] != product_code]

    def get_quote(self) -> Dict[str, Any]:
        """Devuelve el presupuesto actual con un resumen y el total."""
        if not self.items:
            return {'items': [], 'total': 0.0, 'message': "El presupuesto está vacío."}

        total_price = sum(item['product']['Precio Final U$D'] * item['quantity'] for item in self.items)

        return {
            'items': self.items,
            'total': round(total_price, 2)
        }

    def clear_quote(self):
        """Limpia el presupuesto."""
        self.items = []
