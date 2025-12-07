# Główny plik uruchomieniowy aplikacji Flask
# Uruchamia serwer deweloperski

import os
from app import create_app
from app.config import DevelopmentConfig, ProductionConfig

# Wybór konfiguracji na podstawie zmiennej środowiskowej
env = os.environ.get('FLASK_ENV', 'development')
config = ProductionConfig if env == 'production' else DevelopmentConfig

# Utworzenie aplikacji
app = create_app(config)

if __name__ == '__main__':
    # TODO: W produkcji użyć WSGI server (gunicorn, uWSGI)
    # Przykład: gunicorn -w 4 -b 0.0.0.0:5000 run:app
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True if env == 'development' else False
    )
