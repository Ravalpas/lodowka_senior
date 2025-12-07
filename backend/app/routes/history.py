# Blueprint dla historii operacji
# Obsługuje przeglądanie historii działań na produktach

from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import OperationHistory, FridgeItem, Product
from ..extensions import db

bp = Blueprint('history', __name__, url_prefix='/history')


@bp.route('/', methods=['GET'])
@jwt_required()
def history_page():
    """
    Wyświetla stronę z historią operacji
    """
    # TODO: Renderować szablon history.html
    return render_template('history.html')


# ==================== NOWE ENDPOINTY API ====================

@bp.route('/api/last_operation', methods=['GET'])
@jwt_required()
def get_last_operation():
    """
    API endpoint - zwraca ostatnią operację użytkownika.
    
    Pobiera ostatni rekord z historia_operacji_pozycji gdzie:
    - uzytkownik_id = user_id (zalogowany użytkownik)
    - sortowanie po utworzono DESC
    - limit 1
    
    Zwraca:
    - exists: bool - czy operacja istnieje
    - type: str - typ operacji (dodano/zuzyto/usunieto)
    - amount: float - ilość
    - unit: str - jednostka
    - comment: str - komentarz
    - created_at: str - data utworzenia (ISO 8601)
    """
    user_id = get_jwt_identity()
    
    # Pobierz ostatnią operację użytkownika
    last_op = (
        db.session.query(OperationHistory)
        .filter(OperationHistory.uzytkownik_id == user_id)
        .order_by(OperationHistory.utworzono.desc())
        .first()
    )
    
    if not last_op:
        return jsonify({"exists": False})
    
    # Pobierz powiązany produkt i jednostkę
    fridge_item = db.session.query(FridgeItem).get(last_op.pozycja_id)
    unit = "szt"  # Domyślna jednostka
    
    if fridge_item:
        product = db.session.query(Product).get(fridge_item.produkt_id)
        if product and product.jednostka:
            unit = product.jednostka
    
    return jsonify({
        "exists": True,
        "type": last_op.typ,
        "amount": float(last_op.ilosc) if last_op.ilosc else 0.0,
        "unit": unit,
        "comment": last_op.komentarz or "",
        "created_at": last_op.utworzono.isoformat() if last_op.utworzono else None
    })


# ==================== POZOSTAŁE ENDPOINTY ====================

@bp.route('/api/operations', methods=['GET'])
@jwt_required()
def get_operation_history():
    """
    API endpoint - zwraca historię operacji użytkownika
    """
    # TODO: Implementować pobieranie historii operacji
    # TODO: Paginacja wyników
    # TODO: Filtry (typ operacji, zakres dat, produkt)
    pass


@bp.route('/api/operations/<int:operation_id>', methods=['GET'])
@jwt_required()
def get_operation_details(operation_id):
    """
    API endpoint - zwraca szczegóły konkretnej operacji
    """
    # TODO: Implementować pobieranie szczegółów operacji
    # TODO: Sprawdzenie uprawnień użytkownika
    pass


@bp.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """
    API endpoint - zwraca statystyki operacji
    """
    # TODO: Implementować generowanie statystyk
    # TODO: Najczęściej dodawane produkty
    # TODO: Najczęściej marnowane produkty
    # TODO: Statystyki w czasie
    pass
