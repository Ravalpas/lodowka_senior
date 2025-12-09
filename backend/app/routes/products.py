# backend/app/routes/products.py
# Routes dla zarządzania produktami w lodówce użytkownika

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import FridgeItem, Lodowka, Product, WartosciOdzywcze
from ..extensions import db
from datetime import datetime

bp = Blueprint('products', __name__, url_prefix='/products')


@bp.route('/', methods=['GET'])
@jwt_required()
def products_page():
    """Strona z listą produktów użytkownika w lodówce"""
    try:
        current_user_id = get_jwt_identity()
        
        # Pobierz lodówkę użytkownika
        lodowka = Lodowka.query.filter_by(wlasciciel_id=current_user_id, usunieto=None).first()
        if not lodowka:
            flash('Nie znaleziono Twojej lodówki', 'error')
            return redirect(url_for('auth.account_page'))
        
        # Pobierz aktywne produkty z lodówki użytkownika
        all_items = db.session.query(FridgeItem)\
            .filter(FridgeItem.lodowka_id == lodowka.id)\
            .filter(FridgeItem.usunieto.is_(None))\
            .all()
        
        # Grupowanie produktów (jak w widoku lodówki)
        # Klucz: (produkt_id, nazwa_wlasna, wazne_do)
        grouped = {}
        
        for item in all_items:
            key = (item.produkt_id, item.nazwa_wlasna, item.wazne_do)
            
            if key not in grouped:
                grouped[key] = {
                    'items': [],
                    'first_created': item.utworzono,
                    'last_created': item.utworzono
                }
            
            grouped[key]['items'].append(item)
            
            # Śledź daty dodania
            if item.utworzono < grouped[key]['first_created']:
                grouped[key]['first_created'] = item.utworzono
            if item.utworzono > grouped[key]['last_created']:
                grouped[key]['last_created'] = item.utworzono
        
        # Formatuj dane do wyświetlenia
        products = []
        for key, data in grouped.items():
            produkt_id, nazwa_wlasna, wazne_do = key
            first_item = data['items'][0]
            
            # Pobierz dane produktu i wartości odżywcze jeśli istnieją
            product = None
            wartosci = None
            if produkt_id:
                product = db.session.query(Product).get(produkt_id)
                if product:
                    wartosci = db.session.query(WartosciOdzywcze).filter_by(produkt_id=product.id).first()
            
            product_dict = {
                'item_id': first_item.id,  # ID pierwszego elementu z grupy
                'product_id': produkt_id,
                'nazwa': nazwa_wlasna or (product.nazwa if product else 'Produkt bez nazwy'),
                'marka': product.marka if product else None,
                'kategoria': product.kategoria if product else None,
                'barcode_13cyf': product.barcode_13cyf if product else None,
                'ilosc': sum(float(item.ilosc) for item in data['items']),  # Suma ilości
                'jednostka': first_item.jednostka_g_ml_szt,
                'wazne_do': wazne_do,
                'utworzono': data['first_created'],  # Data dodania pierwszego
                'zaktualizowano': data['last_created'],  # Data dodania ostatniego
                'wartosci_odzywcze': None
            }
            
            if wartosci:
                product_dict['wartosci_odzywcze'] = {
                    'kcal': float(wartosci.na_100g_kcal) if wartosci.na_100g_kcal else None,
                    'bialko_g': float(wartosci.na_100g_bialko_g) if wartosci.na_100g_bialko_g else None,
                    'tluszcz_g': float(wartosci.na_100g_tluszcz_g) if wartosci.na_100g_tluszcz_g else None,
                    'weglowodany_g': float(wartosci.na_100g_weglowodany_g) if wartosci.na_100g_weglowodany_g else None,
                }
            
            products.append(product_dict)
        
        return render_template('products.html', products=products)
    except Exception as e:
        flash(f'Błąd podczas pobierania produktów: {str(e)}', 'error')
        return redirect(url_for('auth.account_page'))


@bp.route('/<int:item_id>', methods=['GET'])
@jwt_required()
def product_detail(item_id):
    """Strona ze szczegółami zgrupowanego produktu w lodówce"""
    try:
        current_user_id = get_jwt_identity()
        
        # Pobierz lodówkę użytkownika
        lodowka = Lodowka.query.filter_by(wlasciciel_id=current_user_id, usunieto=None).first()
        if not lodowka:
            flash('Nie znaleziono Twojej lodówki', 'error')
            return redirect(url_for('products.products_page'))
        
        # Pobierz pozycję bazową (reprezentacyjną)
        base_item = db.session.query(FridgeItem)\
            .filter(FridgeItem.id == item_id)\
            .filter(FridgeItem.lodowka_id == lodowka.id)\
            .filter(FridgeItem.usunieto.is_(None))\
            .first()
        
        if not base_item:
            flash('Produkt nie znaleziony w Twojej lodówce', 'error')
            return redirect(url_for('products.products_page'))
        
        # Znajdź wszystkie produkty z tej samej grupy
        # Grupujemy po: (produkt_id, nazwa_wlasna, wazne_do)
        grouped_items = db.session.query(FridgeItem)\
            .filter(FridgeItem.lodowka_id == lodowka.id)\
            .filter(FridgeItem.usunieto.is_(None))\
            .filter(FridgeItem.produkt_id == base_item.produkt_id)\
            .filter(FridgeItem.nazwa_wlasna == base_item.nazwa_wlasna)\
            .filter(FridgeItem.wazne_do == base_item.wazne_do)\
            .all()
        
        # Pobierz dane produktu i wartości odżywcze
        product = None
        wartosci = None
        if base_item.produkt_id:
            product = db.session.query(Product).get(base_item.produkt_id)
            if product:
                wartosci = db.session.query(WartosciOdzywcze).filter_by(produkt_id=product.id).first()
        
        # Oblicz sumy i daty
        total_amount = sum(float(item.ilosc) for item in grouped_items)
        first_created = min(item.utworzono for item in grouped_items)
        last_created = max(item.utworzono for item in grouped_items)
        
        product_dict = {
            'item_id': base_item.id,
            'product_id': base_item.produkt_id,
            'nazwa': base_item.nazwa_wlasna or (product.nazwa if product else 'Produkt bez nazwy'),
            'marka': product.marka if product else None,
            'kategoria': product.kategoria if product else None,
            'barcode_13cyf': product.barcode_13cyf if product else None,
            'ilosc': total_amount,
            'jednostka': base_item.jednostka_g_ml_szt,
            'wazne_do': base_item.wazne_do,
            'utworzono': first_created,
            'zaktualizowano': last_created,
            'wartosci_odzywcze': None,
            'wartosci_odzywcze_full': None
        }
        
        if wartosci:
            product_dict['wartosci_odzywcze'] = {
                'kcal': float(wartosci.na_100g_kcal) if wartosci.na_100g_kcal else None,
                'bialko_g': float(wartosci.na_100g_bialko_g) if wartosci.na_100g_bialko_g else None,
                'tluszcz_g': float(wartosci.na_100g_tluszcz_g) if wartosci.na_100g_tluszcz_g else None,
                'weglowodany_g': float(wartosci.na_100g_weglowodany_g) if wartosci.na_100g_weglowodany_g else None,
                'blonnik_g': float(wartosci.na_100g_blonnik_g) if wartosci.na_100g_blonnik_g else None,
                'sol_g': float(wartosci.na_100g_sol_g) if wartosci.na_100g_sol_g else None,
                'zrodlo_id': wartosci.zrodlo_id,
                'pobrano': wartosci.pobrano
            }
            product_dict['wartosci_odzywcze_full'] = wartosci.odp_api
        
        return render_template('product_detail.html', product=product_dict)
    except Exception as e:
        flash(f'Błąd podczas pobierania produktu: {str(e)}', 'error')
        return redirect(url_for('products.products_page'))





@bp.route('/<int:item_id>/delete', methods=['POST'])
@jwt_required()
def delete_product(item_id):
    """Usuwa produkt z lodówki (soft delete)"""
    try:
        current_user_id = get_jwt_identity()
        
        # Znajdź pozycję w lodówce użytkownika
        fridge_item = db.session.query(FridgeItem)\
            .join(Lodowka, FridgeItem.lodowka_id == Lodowka.id)\
            .filter(FridgeItem.id == item_id)\
            .filter(Lodowka.wlasciciel_id == current_user_id)\
            .filter(FridgeItem.usunieto.is_(None))\
            .first()
        
        if not fridge_item:
            flash('Produkt nie znaleziony w Twojej lodówce', 'error')
            return redirect(url_for('products.products_page'))
        
        fridge_item.usunieto = datetime.utcnow()
        fridge_item.usunal_id = current_user_id
        db.session.commit()
        
        flash('Produkt usunięty z lodówki', 'success')
        return redirect(url_for('products.products_page'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Błąd podczas usuwania produktu: {str(e)}', 'error')
        return redirect(url_for('products.products_page'))


@bp.route('/<int:item_id>/enrich', methods=['POST'])
@jwt_required()
def enrich_from_openfoodfacts(item_id):
    """Uzupełnia dane produktu z OpenFoodFacts dla pozycji w lodówce"""
    try:
        current_user_id = get_jwt_identity()
        
        # Znajdź pozycję w lodówce użytkownika i powiązany produkt
        result = db.session.query(FridgeItem, Product)\
            .join(Product, FridgeItem.produkt_id == Product.id)\
            .join(Lodowka, FridgeItem.lodowka_id == Lodowka.id)\
            .filter(FridgeItem.id == item_id)\
            .filter(Lodowka.wlasciciel_id == current_user_id)\
            .filter(FridgeItem.usunieto.is_(None))\
            .first()
        
        if not result:
            flash('Produkt nie znaleziony w Twojej lodówce', 'error')
            return redirect(url_for('products.products_page'))
        
        fridge_item, product = result
        
        if not product.barcode_13cyf:
            flash('Produkt nie ma kodu kreskowego', 'error')
            return redirect(url_for('products.product_detail', item_id=item_id))
        
        # Import ProductService tylko dla tej metody
        from app.services.product_service import ProductService
        
        enrich_result = ProductService.enrich_from_openfoodfacts(product.barcode_13cyf, product.id)
        
        if enrich_result['success']:
            flash(enrich_result['message'], 'success')
        else:
            flash(enrich_result['message'], 'error')
            
        return redirect(url_for('products.product_detail', item_id=item_id))
        
    except Exception as e:
        flash(f'Błąd podczas pobierania danych z OpenFoodFacts: {str(e)}', 'error')
        return redirect(url_for('products.products_page'))


@bp.route('/api/search', methods=['GET'])
@jwt_required()
def search_openfoodfacts_api():
    """API endpoint - wyszukuje produkty w OpenFoodFacts po nazwie"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if not search_term or len(search_term) < 3:
            return jsonify({
                'success': False,
                'message': 'Podaj co najmniej 3 znaki do wyszukania'
            }), 400
        
        from app.services.product_service import ProductService
        result = ProductService.search_openfoodfacts(search_term, page_size=5)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd wyszukiwania: {str(e)}'
        }), 500


@bp.route('/<int:item_id>/assign-barcode', methods=['POST'])
@jwt_required()
def assign_barcode(item_id):
    """Przypisuje kod kreskowy z OpenFoodFacts do produktu i pobiera dane"""
    try:
        current_user_id = get_jwt_identity()
        barcode = request.form.get('barcode')
        
        if not barcode:
            flash('Brak kodu kreskowego', 'error')
            return redirect(url_for('products.products_page'))
        
        # Znajdź lodówkę użytkownika
        lodowka = Lodowka.query.filter_by(wlasciciel_id=current_user_id, usunieto=None).first()
        if not lodowka:
            flash('Nie znaleziono Twojej lodówki', 'error')
            return redirect(url_for('products.products_page'))
        
        # Znajdź pozycję w lodówce
        base_item = db.session.query(FridgeItem)\
            .filter(FridgeItem.id == item_id)\
            .filter(FridgeItem.lodowka_id == lodowka.id)\
            .filter(FridgeItem.usunieto.is_(None))\
            .first()
        
        if not base_item:
            flash('Produkt nie znaleziony w Twojej lodówce', 'error')
            return redirect(url_for('products.products_page'))
        
        # Jeśli produkt nie ma produkt_id, utwórz nowy rekord w tabeli produkty
        if not base_item.produkt_id:
            product = Product(
                nazwa=base_item.nazwa_wlasna,
                barcode_13cyf=barcode,
                domyslna_jednostka_g_ml_szt=base_item.jednostka_g_ml_szt
            )
            db.session.add(product)
            db.session.flush()  # Pobierz ID
            
            # Przypisz produkt_id do wszystkich pozycji z tej samej grupy
            # WAŻNE: Grupujemy po (nazwa_wlasna, wazne_do) - nie łączymy produktów o różnych datach!
            grouped_items = db.session.query(FridgeItem)\
                .filter(FridgeItem.lodowka_id == lodowka.id)\
                .filter(FridgeItem.usunieto.is_(None))\
                .filter(FridgeItem.produkt_id.is_(None))\
                .filter(FridgeItem.nazwa_wlasna == base_item.nazwa_wlasna)\
                .filter(FridgeItem.wazne_do == base_item.wazne_do)\
                .all()
            
            for item in grouped_items:
                item.produkt_id = product.id
        else:
            # Zaktualizuj kod kreskowy istniejącego produktu
            product = db.session.query(Product).get(base_item.produkt_id)
            if not product:
                flash('Błąd: Produkt nie istnieje', 'error')
                return redirect(url_for('products.products_page'))
            
            product.barcode_13cyf = barcode
        
        db.session.commit()
        
        # Pobierz dane z OpenFoodFacts
        from app.services.product_service import ProductService
        enrich_result = ProductService.enrich_from_openfoodfacts(barcode, product.id)
        
        if enrich_result['success']:
            # Zaktualizuj nazwę produktu jeśli została pobrana z API
            if enrich_result.get('data', {}).get('nazwa'):
                product.nazwa = enrich_result['data']['nazwa']
            if enrich_result.get('data', {}).get('marka'):
                product.marka = enrich_result['data']['marka']
            if enrich_result.get('data', {}).get('kategoria'):
                product.kategoria = enrich_result['data']['kategoria']
            
            db.session.commit()
            flash('Dane produktu zaktualizowane z OpenFoodFacts', 'success')
        else:
            flash(f'Przypisano kod kreskowy, ale nie udało się pobrać danych: {enrich_result["message"]}', 'warning')
        
        return redirect(url_for('products.product_detail', item_id=item_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Błąd podczas przypisywania kodu: {str(e)}', 'error')
        return redirect(url_for('products.products_page'))
