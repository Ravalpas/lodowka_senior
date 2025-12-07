# Inicjalizacja rozszerzeń Flask
# Centralne miejsce do tworzenia instancji rozszerzeń używanych w aplikacji

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# SQLAlchemy - ORM do komunikacji z bazą danych
db = SQLAlchemy()

# JWT Manager - zarządzanie tokenami JWT dla autentykacji
jwt = JWTManager()

# TODO: Dodać inne rozszerzenia w razie potrzeby (np. Flask-CORS, Flask-Migrate)
