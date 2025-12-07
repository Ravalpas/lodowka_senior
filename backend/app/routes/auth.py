# Blueprint dla autentykacji
# Obsługuje logowanie, rejestrację i zarządzanie sesją użytkownika

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, set_access_cookies, 
    unset_jwt_cookies
)
from ..services.auth_service import AuthService

bp = Blueprint('auth', __name__)


@bp.route('/')
def home():
    """
    Strona główna - landing page
    """
    return render_template('home.html')


@bp.route('/login', methods=['GET'])
def login_page():
    """
    Wyświetla stronę logowania
    """
    return render_template('login.html')


@bp.route('/login', methods=['POST'])
def login():
    """
    API endpoint dla logowania użytkownika
    """
    try:
        # Pobierz dane z formularza
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Proszę podać email i hasło', 'error')
            return redirect(url_for('auth.login_page'))
        
        # Uwierzytelnienie
        result = AuthService.authenticate_user(email, password)
        
        if not result:
            flash('Nieprawidłowy email lub hasło', 'error')
            return redirect(url_for('auth.login_page'))
        
        # Utworzenie odpowiedzi z przekierowaniem
        response = redirect(url_for('auth.dashboard'))
        
        # Ustawienie cookie z tokenem JWT
        set_access_cookies(response, result['access_token'])
        
        # Flash message tylko na dashboard - zniknie po 3 sekundach
        return response
        
    except Exception as e:
        flash(f'Błąd podczas logowania: {str(e)}', 'error')
        return redirect(url_for('auth.login_page'))


@bp.route('/register', methods=['GET'])
def register_page():
    """
    Wyświetla formularz rejestracji
    """
    return render_template('register.html')


@bp.route('/register', methods=['POST'])
def register():
    """
    API endpoint dla rejestracji nowego użytkownika
    """
    try:
        # Pobierz dane z formularza
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        imie = request.form.get('imie')
        nazwisko = request.form.get('nazwisko')
        
        # Rejestracja
        new_user = AuthService.register_user(
            email=email,
            password=password,
            password_confirm=password_confirm,
            imie=imie,
            nazwisko=nazwisko
        )
        
        if new_user:
            flash('Konto zostało utworzone pomyślnie! Możesz się teraz zalogować.', 'success')
            return redirect(url_for('auth.login_page'))
        else:
            flash('Błąd podczas rejestracji', 'error')
            return redirect(url_for('auth.register_page'))
            
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('auth.register_page'))
    except Exception as e:
        flash(f'Błąd podczas rejestracji: {str(e)}', 'error')
        return redirect(url_for('auth.register_page'))


@bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """
    API endpoint dla wylogowania użytkownika
    """
    response = redirect(url_for('auth.home'))
    unset_jwt_cookies(response)
    flash('Zostałeś wylogowany', 'info')
    return response


@bp.route('/dashboard')
@jwt_required()
def dashboard():
    """
    Panel użytkownika - dostępny tylko dla zalogowanych
    """
    # Pobierz ID zalogowanego użytkownika z JWT
    current_user_id = get_jwt_identity()
    
    # Pobierz dane użytkownika
    user = AuthService.get_user_by_id(current_user_id)
    
    if not user:
        flash('Nie znaleziono użytkownika', 'error')
        return redirect(url_for('auth.login_page'))
    
    return render_template('dashboard.html', user=user)


@bp.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Zwraca informacje o zalogowanym użytkowniku (API)
    """
    current_user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(current_user_id)
    
    if not user:
        return jsonify({'error': 'Użytkownik nie znaleziony'}), 404
    
    return jsonify(user.to_dict()), 200
