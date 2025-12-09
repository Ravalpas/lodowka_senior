# Plik inicjalizacyjny modułu routes
# Importuje wszystkie blueprinty dla łatwiejszego dostępu

from . import auth
from . import fridge
from . import history
from . import logs
from . import products
from . import ai

__all__ = ['auth', 'fridge', 'history', 'logs', 'products', 'ai']
