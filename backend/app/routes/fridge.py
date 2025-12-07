# Blueprint dla operacji na lodówce
# Obsługuje zarządzanie produktami w lodówce

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import func
from ..models import FridgeItem, Lodowka, User, Product
from ..extensions import db

bp = Blueprint('fridge', __name__, url_prefix='/fridge')


# ==================== FUNKCJE POMOCNICZE ====================

def normalize_to_base_unit(amount, unit):
    """
    Normalizuje ilość do podstawowej jednostki dla precyzyjnego sumowania.
    - g, kg → mg (miligramy)
    - ml, l → µl (mikrolitry)
    - szt → szt (bez zmian)
    
    Returns: (amount_in_base_unit, base_unit_type)
    """
    if unit in ['g', 'kg']:
        # Waga: mg jako podstawa
        if unit == 'kg':
            return amount * 1000000, 'weight'  # 1kg = 1000g = 1000000mg
        else:  # unit == 'g'
            return amount * 1000, 'weight'  # 1g = 1000mg
    elif unit in ['ml', 'l']:
        # Objętość: µl jako podstawa
        if unit == 'l':
            return amount * 1000000, 'volume'  # 1l = 1000ml = 1000000µl
        else:  # unit == 'ml'
            return amount * 1000, 'volume'  # 1ml = 1000µl
    else:  # unit == 'szt'
        return amount, 'piece'


def format_amount_display(amount_mg_or_ul, unit_type):
    """
    Formatuje ilość do najlepszej jednostki wyświetlania.
    - weight: mg → g lub kg
    - volume: µl → ml lub l
    - piece: bez zmian
    
    Returns: (formatted_amount, display_unit)
    """
    if unit_type == 'weight':
        # amount_mg_or_ul jest w miligramach
        if amount_mg_or_ul >= 1000000:  # >= 1kg
            return round(amount_mg_or_ul / 1000000, 2), 'kg'
        else:
            return round(amount_mg_or_ul / 1000, 1), 'g'
    elif unit_type == 'volume':
        # amount_mg_or_ul jest w mikrolitrach
        if amount_mg_or_ul >= 1000000:  # >= 1l
            return round(amount_mg_or_ul / 1000000, 2), 'l'
        else:
            return round(amount_mg_or_ul / 1000, 1), 'ml'
    else:  # piece
        return int(amount_mg_or_ul), 'szt'


@bp.route('/', methods=['GET'])
@jwt_required(optional=True)
def fridge_page():
    """
    Wyświetla stronę z zawartością lodówki z sumowaniem produktów.
    Wymaga zalogowania - przekierowuje niezalogowanych na /login.
    
    LOGIKA SUMOWANIA:
    Sumuje pozycje jeśli mają:
    - to samo produkt_id lub tę samą nazwa_wlasna
    - tę samą jednostka_g_ml_szt
    - tę samą wazne_do
    - to samo lodowka_id
    
    Zwraca dane do template fridge.html z listą zsumowanych produktów.
    """
    from flask import flash
    
    # Sprawdź czy użytkownik jest zalogowany
    user_id = get_jwt_identity()
    if not user_id:
        flash('Musisz się zalogować, aby przeglądać lodówkę', 'error')
        return redirect(url_for('auth.login_page'))
    
    # Znajdź lodówkę użytkownika
    lodowka = (
        db.session.query(Lodowka)
        .filter(Lodowka.wlasciciel_id == user_id)
        .filter(Lodowka.usunieto.is_(None))
        .first()
    )
    
    if not lodowka:
        # Jeśli użytkownik nie ma lodówki, renderuj pustą stronę
        return render_template('fridge.html', items=[])
    
    # Pobierz wszystkie aktywne pozycje w lodówce użytkownika
    # UWAGA: Sumujemy ręcznie z konwersją jednostek (g+kg, ml+l)
    all_items = (
        db.session.query(FridgeItem)
        .filter(FridgeItem.lodowka_id == lodowka.id)
        .filter(FridgeItem.usunieto.is_(None))
        .all()
    )
    
    # Grupowanie ręczne z konwersją jednostek
    # Klucz: (produkt_id, nazwa_wlasna, wazne_do)
    # Wartość: {amount_in_base: float, unit_type: str, repr_id: int}
    grouped = {}
    
    for item in all_items:
        # Klucz grupowania: produkt + data ważności
        key = (item.produkt_id, item.nazwa_wlasna, item.wazne_do)
        
        # Normalizuj do jednostki podstawowej
        base_amount, unit_type = normalize_to_base_unit(
            item.ilosc, 
            item.jednostka_g_ml_szt
        )
        
        if key not in grouped:
            grouped[key] = {
                'base_amount': 0,
                'unit_type': unit_type,
                'repr_id': item.id
            }
        
        # Sumuj w jednostce podstawowej
        grouped[key]['base_amount'] += base_amount
    
    # Przygotuj dane dla template
    items_data = []
    dzisiaj = date.today()
    jutro = dzisiaj + timedelta(days=1)
    pojutrze = dzisiaj + timedelta(days=2)
    
    for key, data in grouped.items():
        produkt_id, nazwa_wlasna, wazne_do = key
        
        # Pobierz nazwę produktu z tabeli produkty jeśli istnieje
        display_name = nazwa_wlasna
        if produkt_id:
            product = db.session.query(Product).get(produkt_id)
            if product:
                display_name = f"{product.nazwa} ({product.marka or 'bez marki'})"
        
        # Sformatuj ilość do najlepszej jednostki
        display_amount, display_unit = format_amount_display(
            data['base_amount'],
            data['unit_type']
        )
        
        # Określ status wygasania
        expiry_status = "ok"  # zielony
        if wazne_do:
            if wazne_do < dzisiaj:
                expiry_status = "expired"  # czerwony
            elif wazne_do == dzisiaj:
                expiry_status = "today"  # pomarańczowy
            elif wazne_do == jutro:
                expiry_status = "tomorrow"  # żółty
            elif wazne_do <= pojutrze:
                expiry_status = "soon"  # jasnopomarańczowy
        
        items_data.append({
            'id': data['repr_id'],
            'produkt_id': produkt_id,
            'nazwa': display_name or 'Produkt bez nazwy',
            'nazwa_wlasna': nazwa_wlasna,
            'ilosc': display_amount,
            'jednostka': display_unit,
            'wazne_do': wazne_do.strftime('%Y-%m-%d') if wazne_do else None,
            'expiry_status': expiry_status
        })
    
    return render_template('fridge.html', items=items_data)


# ==================== NOWE ENDPOINTY API ====================

@bp.route('/api/count', methods=['GET'])
@jwt_required()
def get_fridge_count():
    """
    API endpoint - zwraca liczb\u0119 aktywnych produktów w lodówce użytkownika.
    
    Zlicza produkty z tabeli magazyn_pozycje_lodowki gdzie:
    - lodowka.wlasciciel_id = user_id (zalogowany użytkownik)
    - magazyn_pozycje_lodowki.usunieto IS NULL (nie usunięte)
    """
    user_id = int(get_jwt_identity())
    
    # Zlicz produkty w lodówce użytkownika
    count = (
        db.session.query(func.count(FridgeItem.id))
        .join(Lodowka, FridgeItem.lodowka_id == Lodowka.id)
        .filter(Lodowka.wlasciciel_id == user_id)
        .filter(FridgeItem.usunieto.is_(None))
        .scalar()
    )
    
    return jsonify({"count": count or 0})


@bp.route('/api/expiring_soon_count', methods=['GET'])
@jwt_required()
def get_expiring_soon_count():
    """
    API endpoint - zwraca liczb\u0119 produktów wygasających jutro.
    
    Zlicza produkty gdzie:
    - wazne_do == jutro (tylko data, bez czasu)
    - lodowka.wlasciciel_id = user_id
    - usunieto IS NULL
    """
    user_id = int(get_jwt_identity())
    
    # Oblicz datę jutrzejszą
    jutro = date.today() + timedelta(days=1)
    
    # Zlicz produkty wygasające jutro
    count = (
        db.session.query(func.count(FridgeItem.id))
        .join(Lodowka, FridgeItem.lodowka_id == Lodowka.id)
        .filter(Lodowka.wlasciciel_id == user_id)
        .filter(FridgeItem.usunieto.is_(None))
        .filter(FridgeItem.wazne_do.isnot(None))
        .filter(FridgeItem.wazne_do == jutro)
        .scalar()
    )
    
    return jsonify({"count": count or 0})


@bp.route('/api/expired_count', methods=['GET'])
@jwt_required()
def get_expired_count():
    """
    API endpoint - zwraca liczb\u0119 przeterminowanych produktów.
    
    Zlicza produkty gdzie:
    - wazne_do < dzisiaj
    - lodowka.wlasciciel_id = user_id
    - usunieto IS NULL
    """
    user_id = int(get_jwt_identity())
    
    # Dzisiejsza data
    dzisiaj = date.today()
    
    # Zlicz przeterminowane produkty
    count = (
        db.session.query(func.count(FridgeItem.id))
        .join(Lodowka, FridgeItem.lodowka_id == Lodowka.id)
        .filter(Lodowka.wlasciciel_id == user_id)
        .filter(FridgeItem.usunieto.is_(None))
        .filter(FridgeItem.wazne_do.isnot(None))
        .filter(FridgeItem.wazne_do < dzisiaj)
        .scalar()
    )
    
    return jsonify({"count": count or 0})


# ==================== DODAWANIE PRODUKTÓW ====================

@bp.route('/add', methods=['GET'])
@jwt_required(optional=True)
def add_fridge_item_page():
    """
    Wyświetla formularz dodawania produktu do lodówki.
    Wymaga zalogowania.
    """
    from flask import flash
    
    user_id = get_jwt_identity()
    if not user_id:
        flash('Musisz się zalogować, aby dodać produkt', 'error')
        return redirect(url_for('auth.login_page'))
    user_id = int(user_id)
    return render_template('fridge_add.html')


@bp.route('/add', methods=['POST'])
@jwt_required(optional=True)
def add_fridge_item():
    """
    Dodaje nowy produkt do lodówki.
    Wymaga zalogowania.
    
    Wymagane pola formularza:
    - nazwa: string (required)
    - ilosc: integer (required)
    - jednostka: 'szt' | 'g' | 'kg' | 'ml' | 'l' (required)
    - wazne_do: date (optional)
    - barcode: string (optional)
    
    Proces:
    1. Znajdź/stwórz lodówkę użytkownika
    2. Wyszukaj produkt po barcode lub nazwie
    3. Stwórz pozycję w magazyn_pozycje_lodowki
    4. Zapisz wpis w historia_operacji_pozycji
    """
    from flask import flash
    
    user_id = get_jwt_identity()
    if not user_id:
        flash('Musisz się zalogować', 'error')
        return redirect(url_for('auth.login_page'))
    user_id = int(user_id)
    
    # Pobierz dane z formularza
    nazwa = request.form.get('nazwa')
    ilosc = request.form.get('ilosc')
    jednostka = request.form.get('jednostka')
    wazne_do_str = request.form.get('wazne_do')
    barcode = request.form.get('barcode')
    
    # Walidacja
    if not nazwa or not ilosc or not jednostka:
        return render_template('fridge_add.html', error='Wypełnij wszystkie wymagane pola'), 400
    
    try:
        ilosc = int(ilosc)
        if ilosc <= 0:
            raise ValueError()
    except ValueError:
        return render_template('fridge_add.html', error='Ilość musi być dodatnią liczbą'), 400
    
    if jednostka not in ['szt', 'g', 'kg', 'ml', 'l']:
        return render_template('fridge_add.html', error='Nieprawidłowa jednostka'), 400
    
    # Parsuj datę ważności
    wazne_do = None
    if wazne_do_str:
        try:
            wazne_do = datetime.strptime(wazne_do_str, '%Y-%m-%d').date()
        except ValueError:
            return render_template('fridge_add.html', error='Nieprawidłowy format daty'), 400
    
    # Znajdź/stwórz lodówkę użytkownika
    lodowka = (
        db.session.query(Lodowka)
        .filter(Lodowka.wlasciciel_id == user_id)
        .filter(Lodowka.usunieto.is_(None))
        .first()
    )
    
    if not lodowka:
        lodowka = Lodowka(wlasciciel_id=user_id)
        db.session.add(lodowka)
        db.session.flush()  # Generuje ID
    
    # Wyszukaj produkt po barcode lub nazwie
    product = None
    if barcode:
        product = db.session.query(Product).filter(Product.barcode_13cyf == barcode).first()
    if not product:
        product = db.session.query(Product).filter(Product.nazwa == nazwa).first()
    
    # Stwórz nową pozycję w lodówce
    from ..models import OperationHistory
    
    new_item = FridgeItem(
        lodowka_id=lodowka.id,
        produkt_id=product.id if product else None,
        nazwa_wlasna=nazwa,
        ilosc=ilosc,
        jednostka_g_ml_szt=jednostka,
        wazne_do=wazne_do,
        jak_dodano_pozycje='manual',
        dodal_uzytkownik_id=user_id
    )
    
    db.session.add(new_item)
    db.session.flush()  # Generuje ID
    
    # Zapisz w historii operacji
    history_entry = OperationHistory(
        pozycja_id=new_item.id,
        typ='dodano',
        ilosc=ilosc,
        jednostka_g_ml_szt=jednostka,
        komentarz='Dodano pozycję',
        uzytkownik_id=user_id
    )
    db.session.add(history_entry)
    
    try:
        db.session.commit()
        return render_template('fridge_add.html', success='Produkt został dodany!'), 200
    except Exception as e:
        db.session.rollback()
        return render_template('fridge_add.html', error=f'Błąd: {str(e)}'), 500


# ==================== ZUŻYWANIE PRODUKTÓW ====================

@bp.route('/consume/<int:item_id>', methods=['POST'])
@jwt_required(optional=True)
def consume_fridge_item(item_id):
    """
    Zużywa określoną ilość produktu lub z całej grupy.
    
    UWAGA: Ilość podana w formularzu jest w jednostce WYŚWIETLANEJ (po konwersji).
    Funkcja musi przekonwertować z powrotem do jednostek bazowych i rozdzielić
    zużycie proporcjonalnie między pozycje w grupie.
    
    Proces:
    1. Sprawdź uprawnienia użytkownika
    2. Pobierz wszystkie pozycje z grupy (ten sam produkt + data ważności)
    3. Przekonwertuj ilość do zużycia z jednostki wyświetlanej do bazowej
    4. Rozdziel zużycie proporcjonalnie między pozycje
    5. Zmniejsz ilość w magazynie, usuń pozycje z ilością <= 0
    6. Zapisz w historia_operacji_pozycji
    """
    from flask import flash
    
    user_id = get_jwt_identity()
    if not user_id:
        flash('Musisz się zalogować', 'error')
        return redirect(url_for('auth.login_page'))
    user_id = int(user_id)
    
    # Pobierz pozycję reprezentatywną
    item = db.session.query(FridgeItem).get(item_id)
    
    if not item or item.usunieto:
        return "Produkt nie istnieje", 404
    
    # Sprawdź uprawnienia (czy to lodówka użytkownika)
    lodowka = db.session.query(Lodowka).get(item.lodowka_id)
    if not lodowka:
        return "Lodówka nie istnieje", 404
        
    if lodowka.wlasciciel_id != user_id:
        return f"Brak uprawnień - lodówka należy do użytkownika {lodowka.wlasciciel_id}, a ty jesteś {user_id}", 403
    
    # Pobierz ilość do zużycia (w jednostce WYŚWIETLANEJ)
    ilosc_str = request.form.get('ilosc')
    try:
        ilosc_do_zuzycia_display = float(ilosc_str)
        if ilosc_do_zuzycia_display <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return "Nieprawidłowa ilość", 400
    
    # Znajdź wszystkie pozycje z tej samej grupy
    group_items = (
        db.session.query(FridgeItem)
        .filter(FridgeItem.lodowka_id == lodowka.id)
        .filter(FridgeItem.usunieto.is_(None))
        .filter(
            (FridgeItem.produkt_id == item.produkt_id) if item.produkt_id 
            else (FridgeItem.nazwa_wlasna == item.nazwa_wlasna)
        )
        .filter(FridgeItem.wazne_do == item.wazne_do)
        .all()
    )
    
    if not group_items:
        return "Nie znaleziono pozycji do zużycia", 404
    
    # Oblicz sumę w jednostce bazowej
    total_base = 0
    unit_type = None
    for pos in group_items:
        base, utype = normalize_to_base_unit(pos.ilosc, pos.jednostka_g_ml_szt)
        total_base += base
        if unit_type is None:
            unit_type = utype
    
    # Określ jednostkę wyświetlaną (jaka była użyta)
    display_amount, display_unit = format_amount_display(total_base, unit_type)
    
    # Przekonwertuj ilość do zużycia z jednostki wyświetlanej do bazowej
    # np. użytkownik wpisał "1.2" i jednostka wyświetlana to "kg"
    # musimy przekonwertować 1.2 kg -> mg
    to_consume_base, _ = normalize_to_base_unit(ilosc_do_zuzycia_display, display_unit)
    
    # Sprawdź czy nie zużywamy więcej niż mamy
    if to_consume_base > total_base:
        return "Nie możesz zużyć więcej niż posiadasz", 400
    
    from ..models import OperationHistory
    
    # Rozdziel zużycie proporcjonalnie między pozycje
    remaining_to_consume = to_consume_base
    
    for pos in group_items:
        if remaining_to_consume <= 0:
            break
        
        # Ile ma ta pozycja w jednostce bazowej?
        pos_base, _ = normalize_to_base_unit(pos.ilosc, pos.jednostka_g_ml_szt)
        
        # Ile zużywamy z tej pozycji?
        consume_from_this = min(remaining_to_consume, pos_base)
        
        # Przekonwertuj z jednostki bazowej na oryginalną
        if pos.jednostka_g_ml_szt in ['g', 'kg']:
            if pos.jednostka_g_ml_szt == 'kg':
                consumed_in_original = Decimal(str(consume_from_this / 1000000))
            else:  # g
                consumed_in_original = Decimal(str(consume_from_this / 1000))
        elif pos.jednostka_g_ml_szt in ['ml', 'l']:
            if pos.jednostka_g_ml_szt == 'l':
                consumed_in_original = Decimal(str(consume_from_this / 1000000))
            else:  # ml
                consumed_in_original = Decimal(str(consume_from_this / 1000))
        else:  # szt
            consumed_in_original = Decimal(str(consume_from_this))
        
        # Zmniejsz ilość
        pos.ilosc -= consumed_in_original
        remaining_to_consume -= consume_from_this
        
        # Zapisz w historii
        history_entry = OperationHistory(
            pozycja_id=pos.id,
            typ='zuzyto',
            ilosc=consumed_in_original,
            jednostka_g_ml_szt=pos.jednostka_g_ml_szt,
            komentarz=f'Zużyto {consumed_in_original} {pos.jednostka_g_ml_szt} z pozycji',
            uzytkownik_id=user_id
        )
        db.session.add(history_entry)
        
        # Jeśli zużyto całość (z małym marginesem błędu), oznacz jako usunięte
        if pos.ilosc <= 0.001:
            pos.usunieto = datetime.now()
            pos.usunal_id = user_id
    
    try:
        db.session.commit()
        # Sprawdź skąd przyszło żądanie
        referer = request.referrer or ''
        if 'expiring' in referer:
            return redirect(url_for('fridge.expiring_page'))
        else:
            return redirect(url_for('fridge.fridge_page'))
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"BŁĄD w consume_fridge_item: {str(e)}")
        print(error_details)
        return f"Błąd: {str(e)}<br><pre>{error_details}</pre>", 500


# ==================== WYRZUCANIE PRODUKTÓW ====================

@bp.route('/discard/<int:item_id>', methods=['POST'])
@jwt_required(optional=True)
def discard_fridge_item(item_id):
    """
    Wyrzuca produkt lub całą grupę produktów (soft delete).
    
    Jeśli request zawiera parametr 'group=true', wyrzuca wszystkie pozycje 
    z tym samym produkt_id/nazwa_wlasna i wazne_do.
    
    Proces:
    1. Sprawdź uprawnienia
    2. Ustaw usunieto i usunal_id (dla jednej pozycji lub grupy)
    3. Zapisz w historia_operacji_pozycji
    """
    from flask import flash
    
    user_id = get_jwt_identity()
    if not user_id:
        flash('Musisz się zalogować', 'error')
        return redirect(url_for('auth.login_page'))
    user_id = int(user_id)
    
    # Pobierz pozycję reprezentatywną
    item = db.session.query(FridgeItem).get(item_id)
    
    if not item or item.usunieto:
        return "Produkt nie istnieje", 404
    
    # Sprawdź uprawnienia
    lodowka = db.session.query(Lodowka).get(item.lodowka_id)
    if not lodowka:
        return "Lodówka nie istnieje", 404
        
    if lodowka.wlasciciel_id != user_id:
        return f"Brak uprawnień - lodówka należy do użytkownika {lodowka.wlasciciel_id}, a ty jesteś {user_id}", 403
    
    from ..models import OperationHistory
    
    # Sprawdź czy wyrzucamy całą grupę
    discard_group = request.form.get('group') == 'true' or request.args.get('group') == 'true'
    
    items_to_discard = []
    
    if discard_group:
        # Znajdź wszystkie pozycje z tą samą grupą (produkt + data ważności)
        items_to_discard = (
            db.session.query(FridgeItem)
            .filter(FridgeItem.lodowka_id == lodowka.id)
            .filter(FridgeItem.usunieto.is_(None))
            .filter(
                (FridgeItem.produkt_id == item.produkt_id) if item.produkt_id 
                else (FridgeItem.nazwa_wlasna == item.nazwa_wlasna)
            )
            .filter(FridgeItem.wazne_do == item.wazne_do)
            .all()
        )
    else:
        # Tylko jedna pozycja
        items_to_discard = [item]
    
    # Wyrzuć wszystkie pozycje
    for pos in items_to_discard:
        pos.usunieto = datetime.now()
        pos.usunal_id = user_id
        
        # Zapisz w historii
        history_entry = OperationHistory(
            pozycja_id=pos.id,
            typ='usunieto',
            ilosc=pos.ilosc,
            jednostka_g_ml_szt=pos.jednostka_g_ml_szt,
            komentarz='Usunięto pozycję' if not discard_group else 'Usunięto grupę produktów',
            uzytkownik_id=user_id
        )
        db.session.add(history_entry)
    
    try:
        db.session.commit()
        # Sprawdź skąd przyszło żądanie i przekieruj odpowiednio
        referer = request.referrer or ''
        if 'expiring' in referer:
            return redirect(url_for('fridge.expiring_page'))
        else:
            return redirect(url_for('fridge.fridge_page'))
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"BŁĄD w discard_fridge_item: {str(e)}")
        print(error_details)
        return f"Błąd: {str(e)}<br><pre>{error_details}</pre>", 500


# ==================== POZOSTAŁE ENDPOINTY ====================

@bp.route('/api/items', methods=['GET'])
@jwt_required()
def get_fridge_items():
    """
    API endpoint - zwraca wszystkie produkty w lodówce użytkownika
    """
    # TODO: Implementować pobieranie produktów z bazy
    # TODO: Filtrowanie po użytkowniku
    # TODO: Opcjonalne filtry (kategoria, status, etc.)
    pass


@bp.route('/api/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_fridge_item(item_id):
    """
    API endpoint - aktualizuje istniejący produkt
    """
    # TODO: Implementować aktualizację produktu
    # TODO: Sprawdzenie uprawnień użytkownika
    # TODO: Zapis do historii operacji
    pass


@bp.route('/api/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_fridge_item(item_id):
    """
    API endpoint - usuwa produkt z lodówki
    """
    # TODO: Implementować usuwanie produktu
    # TODO: Sprawdzenie uprawnień użytkownika
    # TODO: Zapis do historii operacji
    pass


@bp.route('/expiring', methods=['GET'])
@jwt_required(optional=True)
def expiring_page():
    """
    Wyświetla stronę z produktami zbliżającymi się do daty ważności.
    Wymaga zalogowania.
    
    Pokazuje produkty które wygasają w ciągu 2 dni (dzisiaj, jutro, pojutrze).
    """
    from flask import flash
    
    user_id = get_jwt_identity()
    if not user_id:
        flash('Musisz się zalogować, aby przeglądać produkty', 'error')
        return redirect(url_for('auth.login_page'))
    user_id = int(user_id)
    user_id = int(user_id)
    
    # Znajdź lodówkę użytkownika
    lodowka = (
        db.session.query(Lodowka)
        .filter(Lodowka.wlasciciel_id == user_id)
        .filter(Lodowka.usunieto.is_(None))
        .first()
    )
    
    if not lodowka:
        return render_template('expiring.html', items=[])
    
    # Daty
    dzisiaj = date.today()
    pojutrze = dzisiaj + timedelta(days=2)
    
    # Pobierz wszystkie produkty wygasające w ciągu 2 dni
    all_items = (
        db.session.query(FridgeItem)
        .filter(FridgeItem.lodowka_id == lodowka.id)
        .filter(FridgeItem.usunieto.is_(None))
        .filter(FridgeItem.wazne_do.isnot(None))
        .filter(FridgeItem.wazne_do <= pojutrze)
        .all()
    )
    
    # Grupowanie z konwersją jednostek (jak w fridge_page)
    # Klucz: (produkt_id, nazwa_wlasna, wazne_do)
    grouped = {}
    
    for item in all_items:
        key = (item.produkt_id, item.nazwa_wlasna, item.wazne_do)
        
        base_amount, unit_type = normalize_to_base_unit(
            item.ilosc, 
            item.jednostka_g_ml_szt
        )
        
        if key not in grouped:
            grouped[key] = {
                'base_amount': 0,
                'unit_type': unit_type,
                'repr_id': item.id
            }
        
        grouped[key]['base_amount'] += base_amount
    
    # Przygotuj dane
    items_data = []
    jutro = dzisiaj + timedelta(days=1)
    
    for key, data in grouped.items():
        produkt_id, nazwa_wlasna, wazne_do = key
        
        # Pobierz nazwę produktu
        display_name = nazwa_wlasna
        if produkt_id:
            product = db.session.query(Product).get(produkt_id)
            if product:
                display_name = f"{product.nazwa} ({product.marka or 'bez marki'})"
        
        # Sformatuj ilość
        display_amount, display_unit = format_amount_display(
            data['base_amount'],
            data['unit_type']
        )
        
        # Status wygasania
        if wazne_do < dzisiaj:
            expiry_status = "expired"
            days_left = "Przeterminowane"
        elif wazne_do == dzisiaj:
            expiry_status = "today"
            days_left = "Wygasa dzisiaj"
        elif wazne_do == jutro:
            expiry_status = "tomorrow"
            days_left = "Wygasa jutro"
        else:
            expiry_status = "soon"
            days_diff = (wazne_do - dzisiaj).days
            days_left = f"Wygasa za {days_diff} dni"
        
        items_data.append({
            'id': data['repr_id'],
            'nazwa': display_name or 'Produkt bez nazwy',
            'ilosc': display_amount,
            'jednostka': display_unit,
            'wazne_do': wazne_do.strftime('%Y-%m-%d'),
            'expiry_status': expiry_status,
            'days_left': days_left
        })
    
    # Sortuj po dacie ważności
    items_data.sort(key=lambda x: x['wazne_do'])
    
    return render_template('expiring.html', items=items_data)


@bp.route('/api/expiring', methods=['GET'])
@jwt_required()
def get_expiring_items():
    """
    API endpoint - zwraca produkty zbliżające się do terminu ważności
    """
    # TODO: Implementować pobieranie produktów wygasających
    # TODO: Parametr dni do wygaśnięcia (np. 3, 7 dni)
    pass
