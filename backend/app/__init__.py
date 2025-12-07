# Plik inicjalizacyjny aplikacji Flask
# Tworzy obiekt aplikacji Flask i rejestruje rozszerzenia oraz blueprinty

from flask import Flask
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from .extensions import db, jwt
from .config import Config


def create_app(config_class=Config):
    """
    Factory pattern dla aplikacji Flask
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicjalizacja rozszerzeń
    db.init_app(app)
    jwt.init_app(app)
    
    # Context processor - dodaje zmienne dostępne w wszystkich szablonach
    @app.context_processor
    def inject_user_status():
        """Sprawdza czy użytkownik jest zalogowany i udostępnia to w szablonach"""
        from flask import request
        from .models import User
        
        # Strony które zawsze mają pokazywać tylko przycisk "Wróć na stronę główną"
        public_pages = ['auth.login_page', 'auth.register_page', 'auth.home']
        
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            
            # Na stronach publicznych (login/register) zawsze pokazuj uproszczoną nawigację
            if request.endpoint in public_pages:
                return {'user_logged_in': False, 'user_name': None}
            
            if user_id:
                # Pobierz imię użytkownika z bazy
                user = db.session.query(User).get(int(user_id))
                user_name = user.imie if user and user.imie else None
                return {'user_logged_in': True, 'user_name': user_name}
            
            return {'user_logged_in': False, 'user_name': None}
        except:
            return {'user_logged_in': False, 'user_name': None}
    
    # Rejestracja blueprintów
    from .routes import auth, fridge, history, logs
    app.register_blueprint(auth.bp)
    app.register_blueprint(fridge.bp)
    app.register_blueprint(history.bp)
    app.register_blueprint(logs.bp)
    
    # TODO: Dodać obsługę błędów (error handlers)
    # TODO: Dodać CORS jeśli potrzebne
    
    return app
