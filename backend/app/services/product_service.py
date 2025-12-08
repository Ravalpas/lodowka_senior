# backend/app/services/product_service.py
# Serwis zarządzania produktami z integracją OpenFoodFacts API

import requests
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import and_
from ..extensions import db
from ..models import Product, WartosciOdzywcze


class ProductService:
    """Serwis do zarządzania produktami i pobierania danych z OpenFoodFacts"""
    
    OPENFOODFACTS_API_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}"
    
    @staticmethod
    def get_all_products(include_deleted=False) -> List[Dict]:
        """
        Pobiera wszystkie produkty z wartościami odżywczymi
        
        Args:
            include_deleted: Czy uwzględniać usunięte produkty
            
        Returns:
            Lista słowników z danymi produktów i wartościami odżywczymi
        """
        query = db.session.query(Product, WartosciOdzywcze).outerjoin(
            WartosciOdzywcze, Product.id == WartosciOdzywcze.produkt_id
        )
        
        if not include_deleted:
            query = query.filter(Product.usunieto.is_(None))
        
        results = query.all()
        
        products = []
        for product, wartosci in results:
            product_dict = {
                'id': product.id,
                'nazwa': product.nazwa,
                'marka': product.marka,
                'kategoria': product.kategoria,
                'barcode_13cyf': product.barcode_13cyf,
                'domyslna_jednostka_g_ml_szt': product.domyslna_jednostka_g_ml_szt,
                'gramow_na_szt': float(product.gramow_na_szt) if product.gramow_na_szt else None,
                'utworzono': product.utworzono,
                'zaktualizowano': product.zaktualizowano,
                'wartosci_odzywcze': None
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
            
            products.append(product_dict)
        
        return products
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Dict]:
        """
        Pobiera szczegóły produktu po ID
        
        Args:
            product_id: ID produktu
            
        Returns:
            Słownik z danymi produktu lub None
        """
        product = Product.query.filter_by(id=product_id, usunieto=None).first()
        if not product:
            return None
        
        wartosci = WartosciOdzywcze.query.filter_by(produkt_id=product_id).first()
        
        product_dict = {
            'id': product.id,
            'nazwa': product.nazwa,
            'marka': product.marka,
            'kategoria': product.kategoria,
            'barcode_13cyf': product.barcode_13cyf,
            'domyslna_jednostka_g_ml_szt': product.domyslna_jednostka_g_ml_szt,
            'gramow_na_szt': float(product.gramow_na_szt) if product.gramow_na_szt else None,
            'utworzono': product.utworzono,
            'zaktualizowano': product.zaktualizowano,
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
        
        return product_dict
    
    @staticmethod
    def enrich_from_openfoodfacts(barcode: str, product_id: Optional[int] = None) -> Dict:
        """
        Pobiera dane z OpenFoodFacts API i zapisuje do bazy
        
        Args:
            barcode: Kod kreskowy produktu
            product_id: Opcjonalnie ID istniejącego produktu
            
        Returns:
            Słownik z wynikiem operacji
        """
        try:
            # Zapytanie do OpenFoodFacts API
            url = ProductService.OPENFOODFACTS_API_URL.format(barcode=barcode)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 1:
                return {
                    'success': False,
                    'message': 'Produkt nie znaleziony w bazie OpenFoodFacts'
                }
            
            product_data = data.get('product', {})
            nutriments = product_data.get('nutriments', {})
            
            # Jeśli nie podano product_id, szukamy istniejącego produktu
            if not product_id:
                product = Product.query.filter_by(barcode_13cyf=barcode, usunieto=None).first()
                if product:
                    product_id = product.id
            
            if not product_id:
                return {
                    'success': False,
                    'message': 'Nie znaleziono produktu w bazie. Najpierw utwórz produkt z tym kodem kreskowym.'
                }
            
            # Sprawdzamy czy istnieją już wartości odżywcze
            wartosci = WartosciOdzywcze.query.filter_by(produkt_id=product_id).first()
            
            if not wartosci:
                wartosci = WartosciOdzywcze(produkt_id=product_id)
                db.session.add(wartosci)
            
            # Aktualizujemy wartości odżywcze
            wartosci.zrodlo_id = 1  # OpenFoodFacts
            wartosci.na_100g_kcal = nutriments.get('energy-kcal_100g') or nutriments.get('energy-kcal')
            wartosci.na_100g_bialko_g = nutriments.get('proteins_100g') or nutriments.get('proteins')
            wartosci.na_100g_tluszcz_g = nutriments.get('fat_100g') or nutriments.get('fat')
            wartosci.na_100g_weglowodany_g = nutriments.get('carbohydrates_100g') or nutriments.get('carbohydrates')
            wartosci.na_100g_blonnik_g = nutriments.get('fiber_100g') or nutriments.get('fiber')
            wartosci.na_100g_sol_g = nutriments.get('salt_100g') or nutriments.get('salt')
            wartosci.odp_api = data
            wartosci.api = product_data
            wartosci.pobrano = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Dane odżywcze zaktualizowane z OpenFoodFacts',
                'data': {
                    'nazwa': product_data.get('product_name'),
                    'marka': product_data.get('brands'),
                    'kategoria': product_data.get('categories')
                }
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'Błąd połączenia z OpenFoodFacts: {str(e)}'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Błąd podczas zapisywania danych: {str(e)}'
            }
    
    @staticmethod
    def create_product(data: Dict) -> Dict:
        """
        Tworzy nowy produkt
        
        Args:
            data: Słownik z danymi produktu
            
        Returns:
            Słownik z wynikiem operacji
        """
        try:
            product = Product(
                nazwa=data.get('nazwa'),
                marka=data.get('marka'),
                kategoria=data.get('kategoria'),
                barcode_13cyf=data.get('barcode_13cyf'),
                domyslna_jednostka_g_ml_szt=data.get('domyslna_jednostka_g_ml_szt', 'g'),
                gramow_na_szt=data.get('gramow_na_szt')
            )
            
            db.session.add(product)
            db.session.commit()
            
            # Jeśli podano kod kreskowy, spróbuj pobrać dane z OpenFoodFacts
            if product.barcode_13cyf:
                ProductService.enrich_from_openfoodfacts(product.barcode_13cyf, product.id)
            
            return {
                'success': True,
                'message': 'Produkt utworzony pomyślnie',
                'product_id': product.id
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Błąd podczas tworzenia produktu: {str(e)}'
            }
    
    @staticmethod
    def update_product(product_id: int, data: Dict) -> Dict:
        """
        Aktualizuje dane produktu
        
        Args:
            product_id: ID produktu
            data: Słownik z nowymi danymi
            
        Returns:
            Słownik z wynikiem operacji
        """
        try:
            product = Product.query.filter_by(id=product_id, usunieto=None).first()
            if not product:
                return {
                    'success': False,
                    'message': 'Produkt nie znaleziony'
                }
            
            product.nazwa = data.get('nazwa', product.nazwa)
            product.marka = data.get('marka', product.marka)
            product.kategoria = data.get('kategoria', product.kategoria)
            product.barcode_13cyf = data.get('barcode_13cyf', product.barcode_13cyf)
            product.domyslna_jednostka_g_ml_szt = data.get('domyslna_jednostka_g_ml_szt', product.domyslna_jednostka_g_ml_szt)
            product.gramow_na_szt = data.get('gramow_na_szt', product.gramow_na_szt)
            product.zaktualizowano = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Produkt zaktualizowany pomyślnie'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Błąd podczas aktualizacji produktu: {str(e)}'
            }
    
    @staticmethod
    def delete_product(product_id: int, user_id: int) -> Dict:
        """
        Soft delete produktu
        
        Args:
            product_id: ID produktu
            user_id: ID użytkownika usuwającego
            
        Returns:
            Słownik z wynikiem operacji
        """
        try:
            product = Product.query.filter_by(id=product_id, usunieto=None).first()
            if not product:
                return {
                    'success': False,
                    'message': 'Produkt nie znaleziony'
                }
            
            product.usunieto = datetime.utcnow()
            product.usunal_id = user_id
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Produkt usunięty pomyślnie'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Błąd podczas usuwania produktu: {str(e)}'
            }
