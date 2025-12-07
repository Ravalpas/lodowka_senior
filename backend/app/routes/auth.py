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


@bp.route('/account')
@jwt_required()
def account_page():
    """
    Panel użytkownika - Moje konto
    """
    from ..models import User, Lodowka, FridgeItem, OperationHistory
    from .. import db
    
    current_user_id = int(get_jwt_identity())
    
    # Pobierz dane użytkownika
    user = db.session.query(User).get(current_user_id)
    
    if not user:
        flash('Nie znaleziono użytkownika', 'error')
        return redirect(url_for('auth.login_page'))
    
    # Statystyki
    # Liczba aktywnych produktów (nie usunięte)
    active_products = db.session.query(FridgeItem).join(
        Lodowka, FridgeItem.lodowka_id == Lodowka.id
    ).filter(
        Lodowka.wlasciciel_id == current_user_id,
        FridgeItem.usunieto == None
    ).count()
    
    # Liczba wszystkich produktów (włącznie z usuniętymi)
    total_products = db.session.query(FridgeItem).join(
        Lodowka, FridgeItem.lodowka_id == Lodowka.id
    ).filter(
        Lodowka.wlasciciel_id == current_user_id
    ).count()
    
    # Liczba operacji
    total_operations = db.session.query(OperationHistory).join(
        FridgeItem, OperationHistory.pozycja_id == FridgeItem.id
    ).join(
        Lodowka, FridgeItem.lodowka_id == Lodowka.id
    ).filter(
        Lodowka.wlasciciel_id == current_user_id
    ).count()
    
    stats = {
        'active_products': active_products,
        'total_products': total_products,
        'total_operations': total_operations
    }
    
    return render_template('account.html', user_data=user, stats=stats)


@bp.route('/account/update', methods=['POST'])
@jwt_required()
def update_profile():
    """
    Aktualizacja danych profilu użytkownika
    """
    from ..models import User
    from .. import db
    from datetime import datetime
    
    current_user_id = int(get_jwt_identity())
    
    user = db.session.query(User).get(current_user_id)
    
    if not user:
        flash('Nie znaleziono użytkownika', 'error')
        return redirect(url_for('auth.account_page'))
    
    # Pobierz dane z formularza
    imie = request.form.get('imie')
    nazwisko = request.form.get('nazwisko')
    
    # Aktualizuj dane
    if imie is not None:
        user.imie = imie.strip() if imie.strip() else None
    if nazwisko is not None:
        user.nazwisko = nazwisko.strip() if nazwisko.strip() else None
    
    user.zaktualizowano = datetime.now()
    
    try:
        db.session.commit()
        flash('Dane zostały zaktualizowane pomyślnie', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Błąd podczas aktualizacji: {str(e)}', 'error')
    
    return redirect(url_for('auth.account_page'))


@bp.route('/account/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Zmiana hasła użytkownika
    """
    from ..models import User
    from .. import db
    from werkzeug.security import check_password_hash, generate_password_hash
    from datetime import datetime
    
    current_user_id = int(get_jwt_identity())
    
    user = db.session.query(User).get(current_user_id)
    
    if not user:
        flash('Nie znaleziono użytkownika', 'error')
        return redirect(url_for('auth.account_page'))
    
    # Pobierz dane z formularza
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Walidacja
    if not current_password or not new_password or not confirm_password:
        flash('Wszystkie pola są wymagane', 'error')
        return redirect(url_for('auth.account_page'))
    
    # Sprawdź aktualne hasło
    if not check_password_hash(user.haslo_hash, current_password):
        flash('Aktualne hasło jest nieprawidłowe', 'error')
        return redirect(url_for('auth.account_page'))
    
    # Sprawdź czy nowe hasła się zgadzają
    if new_password != confirm_password:
        flash('Nowe hasło i potwierdzenie nie są identyczne', 'error')
        return redirect(url_for('auth.account_page'))
    
    # Sprawdź długość hasła
    if len(new_password) < 6:
        flash('Nowe hasło musi mieć co najmniej 6 znaków', 'error')
        return redirect(url_for('auth.account_page'))
    
    # Zmień hasło
    user.haslo_hash = generate_password_hash(new_password)
    user.zaktualizowano = datetime.now()
    
    try:
        db.session.commit()
        flash('Hasło zostało zmienione pomyślnie', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Błąd podczas zmiany hasła: {str(e)}', 'error')
    
    return redirect(url_for('auth.account_page'))
