# Konfiguracja aplikacji Flask
# Zawiera ustawienia bazy danych, klucze sekretne i inne parametry konfiguracyjne

import os
from datetime import timedelta


class Config:
    """
    Klasa bazowa konfiguracji aplikacji
    """
    # Podstawowe ustawienia Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Konfiguracja bazy danych MySQL
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'lodowka'
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'False') == 'True'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_COOKIE_SECURE = False  # Ustaw True w produkcji (HTTPS)
    JWT_COOKIE_CSRF_PROTECT = False  # Można włączyć dla dodatkowej ochrony
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'
    JWT_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    """
    Konfiguracja dla środowiska deweloperskiego
    """
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """
    Konfiguracja dla środowiska produkcyjnego
    """
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """
    Konfiguracja dla testów
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
