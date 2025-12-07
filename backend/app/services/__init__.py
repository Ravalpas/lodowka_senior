# Plik inicjalizacyjny modułu services
# Importuje wszystkie serwisy dla łatwiejszego dostępu

from .auth_service import AuthService
from .fridge_service import FridgeService
from .product_service import ProductService
from .notification_service import NotificationService

__all__ = ['AuthService', 'FridgeService', 'ProductService', 'NotificationService']
