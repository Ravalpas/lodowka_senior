# Test podstawowy - sprawdza czy aplikacja się uruchamia
# Smoke test dla aplikacji Flask

import sys
import os

# Dodanie ścieżki do głównego pakietu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.config import TestingConfig


def test_app_creation():
    """
    Test sprawdzający czy aplikacja się tworzy
    """
    # TODO: Implementować test tworzenia aplikacji
    app = create_app(TestingConfig)
    assert app is not None
    assert app.config['TESTING'] is True


def test_app_config():
    """
    Test sprawdzający konfigurację aplikacji
    """
    # TODO: Implementować test konfiguracji
    app = create_app(TestingConfig)
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'


# TODO: Dodać więcej testów:
# - Test routingu
# - Test blueprintów
# - Test modeli
# - Test API endpoints
# - Test autentykacji

if __name__ == '__main__':
    # Uruchomienie testów
    # TODO: Zainstalować pytest i używać: pytest backend/tests/
    test_app_creation()
    test_app_config()
    print("Wszystkie testy przeszły pomyślnie!")
