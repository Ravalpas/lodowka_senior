# backend/app/routes/ai.py
# Blueprint dla AI Asystenta Kucharza
# Integracja z lokalnym modelem Ollama (gemma3:4b)

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from datetime import datetime
from ..models import Lodowka, FridgeItem, Product
from ..extensions import db

bp = Blueprint('ai', __name__, url_prefix='/ai')

# Konfiguracja Ollama
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"


def check_ollama_availability():
    """
    Sprawdza czy Ollama jest dostępna.
    
    Returns:
        bool: True jeśli Ollama działa, False w przeciwnym razie
    """
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def calculate_recipes_count(products_count):
    """
    Oblicza liczbę przepisów do wygenerowania na podstawie liczby produktów w lodówce.
    
    Progi:
    - 2-3 produkty → 2 przepisy
    - 4 produkty → 3 przepisy
    - 5 produktów → 4 przepisy
    - 6 produktów → 5 przepisów
    - 7 produktów → 6 przepisów
    - 8 produktów → 7 przepisów
    - 9+ produktów → 8 przepisów
    """
    if products_count < 2:
        return 0  # Za mało produktów
    elif products_count <= 3:
        return 2
    elif products_count == 4:
        return 3
    elif products_count == 5:
        return 4
    elif products_count == 6:
        return 5
    elif products_count == 7:
        return 6
    elif products_count == 8:
        return 7
    else:  # 9+
        return 8


def get_user_fridge_items(user_id):
    """
    Pobiera aktywne produkty z lodówki użytkownika.
    Grupuje produkty tak samo jak w widoku lodówki (po nazwa_wlasna + wazne_do).
    
    Returns:
        Lista słowników z informacjami o produktach:
        - nazwa
        - ilosc
        - jednostka
        - wazne_do
        - marka (jeśli dostępna)
    """
    from collections import defaultdict
    
    # Znajdź lodówkę użytkownika
    lodowka = db.session.query(Lodowka)\
        .filter(Lodowka.wlasciciel_id == user_id)\
        .filter(Lodowka.usunieto.is_(None))\
        .first()
    
    if not lodowka:
        return []
    
    # Pobierz wszystkie aktywne pozycje z lodówki
    all_items = db.session.query(FridgeItem)\
        .filter(FridgeItem.lodowka_id == lodowka.id)\
        .filter(FridgeItem.usunieto.is_(None))\
        .all()
    
    # Grupowanie produktów po (produkt_id, nazwa_wlasna, wazne_do)
    # Klucz: (produkt_id, nazwa_wlasna, wazne_do)
    grouped = defaultdict(lambda: {'ilosc': 0, 'jednostka': None, 'produkt_id': None})
    
    for item in all_items:
        key = (item.produkt_id, item.nazwa_wlasna, item.wazne_do)
        grouped[key]['ilosc'] += float(item.ilosc)
        grouped[key]['jednostka'] = item.jednostka_g_ml_szt
        grouped[key]['produkt_id'] = item.produkt_id
        grouped[key]['wazne_do'] = item.wazne_do
        grouped[key]['nazwa_wlasna'] = item.nazwa_wlasna
    
    # Formatuj dane dla AI
    fridge_contents = []
    for key, data in grouped.items():
        produkt_id, nazwa_wlasna, wazne_do = key
        
        # Pobierz informacje o produkcie z tabeli produkty
        product = None
        if produkt_id:
            product = db.session.query(Product).get(produkt_id)
        
        # Nazwa produktu (z lodówki lub z tabeli produkty)
        nazwa = nazwa_wlasna or (product.nazwa if product else "Nieznany produkt")
        
        # Marka (jeśli dostępna)
        marka = product.marka if product else None
        
        # Formatuj opis produktu
        opis = f"{data['ilosc']:.1f} {data['jednostka']} {nazwa}"
        if marka:
            opis += f" ({marka})"
        if wazne_do:
            opis += f" ważne do {wazne_do.strftime('%Y-%m-%d')}"
        
        fridge_contents.append({
            'nazwa': nazwa,
            'ilosc': data['ilosc'],
            'jednostka': data['jednostka'],
            'wazne_do': wazne_do.strftime('%Y-%m-%d') if wazne_do else None,
            'marka': marka,
            'opis': opis
        })
    
    return fridge_contents


def build_ai_prompt(fridge_items, recipes_count, user_message=None):
    """
    Buduje prompt dla modelu AI z listą produktów i wymaganiami.
    
    Args:
        fridge_items: Lista produktów z lodówki
        recipes_count: Liczba przepisów do wygenerowania
        user_message: Dodatkowe wymagania użytkownika (opcjonalnie)
        
    Returns:
        String z promptem dla AI
    """
    # Lista produktów z lodówki - format: "Sok jabłkowy; Miód; Mleko 3,2%"
    lista_produktow = "; ".join([item['nazwa'] for item in fridge_items])
    
    # Dodatkowe wymagania użytkownika
    wymagania_dodatkowe = ""
    if user_message and user_message.strip():
        wymagania_dodatkowe = f"\n\nDODATKOWE WYMAGANIA UŻYTKOWNIKA:\n{user_message}\n"
    
    prompt = f"""Jesteś doświadczonym kucharzem i dietetykiem. 
Masz wygenerować SENSOWNE domowe przepisy na podstawie produktów z lodówki użytkownika.

PRODUKTY W LODÓWCE (tylko te możesz traktować jako główne składniki):
{lista_produktow}

Zasady OGÓLNE:
- Nie twórz absurdalnych połączeń typu 'sok jabłkowy smażony z miodem'.
- Unikaj przepisów, w których główne składniki to tylko płyny (soki, napoje) bez normalnego jedzenia.
- Nie powtarzaj tego samego składnika w formie oczywiście dublującej się (np. 'jabłko + sok jabłkowy' w jednym deserze, jeśli nie ma to kulinarnego sensu).
- Zakładaj, że użytkownik zawsze ma: sól, pieprz, cukier, olej/oliwę, wodę, podstawowe przyprawy.
- Dopuszczalne jest wskazanie maksymalnie 2 SKŁADNIKÓW do dokupienia na przepis.
- Każdy przepis musi być "normalnym" daniem: śniadanie, obiad, kolacja, przekąska albo deser.
{wymagania_dodatkowe}
KAŻDY PRZEPIS MUSI:
- Wykorzystywać 1–3 produktów z lodówki jako GŁÓWNE składniki.
- Mieć minimum 4 kroki przygotowania.
- Zawierać konkretne czynności (krojenie, smażenie, pieczenie, mieszanie, chłodzenie itp.), z czasami orientacyjnymi.
- Podawać orientacyjną kaloryczność na 100 g (realistyczne wartości, np. 80–500 kcal/100 g, nie 5 lub 2000).

FORMAT ODPOWIEDZI – ZWRACAJ WYŁĄCZNIE PRAWIDŁOWY JSON, BEZ TEKSTU DODATKOWEGO:

{{
  "recipes": [
    {{
      "title": "Nazwa dania",
      "calories_per_100g": 250,
      "ingredients_from_fridge": [
        "Nazwa produktu z lodówki 1",
        "Nazwa produktu z lodówki 2"
      ],
      "ingredients_to_buy": [
        "Składnik do dokupienia 1",
        "Składnik do dokupienia 2"
      ],
      "steps": [
        "Krok 1: ...",
        "Krok 2: ...",
        "Krok 3: ...",
        "Krok 4: ..."
      ]
    }}
  ]
}}

Wypełnij dokładnie ten schemat.
Zwróć dokładnie {recipes_count} przepisów w tablicy "recipes".
ZWRÓĆ TYLKO JSON, bez markdown, bez komentarzy!"""
    
    return prompt


def call_ollama_api(prompt):
    """
    Wywołuje lokalny model Ollama i zwraca wygenerowaną odpowiedź.
    
    Args:
        prompt: Tekst promptu dla modelu
        
    Returns:
        Dict z wynikiem lub błędem
    """
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"  # Wymusza format JSON
        }
        
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=120  # 2 minuty timeout dla większych odpowiedzi
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Ollama zwraca odpowiedź w polu "response"
        ai_response = data.get('response', '')
        
        if not ai_response:
            return {
                'success': False,
                'message': 'Brak odpowiedzi z modelu AI'
            }
        
        # Parsuj JSON z odpowiedzi
        import json
        try:
            recipes_data = json.loads(ai_response)
            return {
                'success': True,
                'data': recipes_data
            }
        except json.JSONDecodeError as e:
            # Jeśli JSON niepoprawny, spróbuj wyciągnąć JSON z tekstu
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                try:
                    recipes_data = json.loads(json_match.group(0))
                    return {
                        'success': True,
                        'data': recipes_data
                    }
                except:
                    pass
            
            return {
                'success': False,
                'message': f'Błąd parsowania JSON z odpowiedzi AI: {str(e)}',
                'raw_response': ai_response[:500]  # Pierwsze 500 znaków do debugowania
            }
        
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'Przekroczono czas oczekiwania na odpowiedź z modelu AI (120s)'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'message': 'Nie można połączyć się z Ollama. Upewnij się, że Ollama działa na http://127.0.0.1:11434'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'message': f'Błąd komunikacji z Ollama: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Nieoczekiwany błąd: {str(e)}'
        }


def generate_fallback_recipes(fridge_items, recipes_count, user_message=None):
    """
    Generuje przykładowe przepisy gdy Ollama nie jest dostępna.
    Używa bardziej zaawansowanej logiki opartej na rzeczywistych produktach.
    
    Args:
        fridge_items: Lista produktów z lodówki
        recipes_count: Liczba przepisów do wygenerowania
        user_message: Dodatkowe wymagania użytkownika (może być None)
        
    Returns:
        Dict z przepisami
    """
    # Pobierz nazwy produktów
    product_names = [item['nazwa'].lower() for item in fridge_items]
    products_str = ', '.join([item['nazwa'] for item in fridge_items])
    
    # Inteligentne przepisy bazujące na rzeczywistych produktach
    recipes = []
    
    # Przepis 1: Jeśli mamy mleko lub nabiał
    if any('mleko' in n or 'jogurt' in n or 'kefir' in n for n in product_names):
        dairy = [item['nazwa'] for item in fridge_items if any(x in item['nazwa'].lower() for x in ['mleko', 'jogurt', 'kefir'])]
        recipes.append({
            'title': 'Koktajl proteinowy',
            'ingredients_from_fridge': dairy[:1],
            'ingredients_to_buy': ['Banan', 'Miód', 'Płatki owsiane (opcjonalnie)'],
            'steps': [
                f'Do blendera wlej {dairy[0] if dairy else "mleko"}',
                'Dodaj banana pokrojonego w plastry',
                'Dodaj łyżeczkę miodu',
                'Opcjonalnie dodaj 2 łyżki płatków owsianych',
                'Zmiksuj przez 30 sekund na wysokich obrotach',
                'Przelej do wysokiej szklanki i podawaj schłodzone'
            ],
            'calories_per_100g': 85
        })
    
    # Przepis 2: Jeśli mamy jajka
    if any('jaj' in n for n in product_names):
        other_ingredients = [item['nazwa'] for item in fridge_items if 'jaj' not in item['nazwa'].lower()][:3]
        recipes.append({
            'title': 'Omlet z dodatkami',
            'ingredients_from_fridge': ['Jajka'] + other_ingredients,
            'ingredients_to_buy': ['Masło', 'Pieczywo'],
            'steps': [
                'Rozbij 2-3 jajka do miski',
                'Dodaj szczyptę soli, pieprzu i 2 łyżki mleka lub wody',
                'Dokładnie roztrzep widelcem',
                f'Pokrój drobno: {", ".join(other_ingredients[:2]) if other_ingredients else "dostępne warzywa"}',
                'Rozgrzej patelnię z łyżeczką masła',
                'Wlej jajka, po chwili dodaj pokrojone składniki',
                'Smaż 3-4 minuty, przewracając na drugą stronę',
                'Podawaj na ciepło z pieczywem'
            ],
            'calories_per_100g': 145
        })
    
    # Przepis 3: Jeśli mamy warzywa lub owoce
    veggies_fruits = [item['nazwa'] for item in fridge_items if any(x in item['nazwa'].lower() 
                      for x in ['cebul', 'pomidor', 'ogór', 'papryka', 'sałat', 'jabł', 'banan', 'marchew'])]
    if veggies_fruits:
        recipes.append({
            'title': 'Świeża sałatka sezonowa',
            'ingredients_from_fridge': veggies_fruits[:4],
            'ingredients_to_buy': ['Oliwa z oliwek', 'Sok z cytryny', 'Sól morska'],
            'steps': [
                'Dokładnie umyj wszystkie składniki pod bieżącą wodą',
                f'Pokrój w kostkę: {", ".join(veggies_fruits[:3])}',
                'Przełóż do dużej miski',
                'Wymieszaj 2 łyżki oliwy z oliwek z sokiem z połowy cytryny',
                'Polej sałatkę sosem',
                'Dodaj szczyptę soli i świeżo zmielonego pieprzu',
                'Delikatnie wymieszaj i podawaj natychmiast'
            ],
            'calories_per_100g': 65
        })
    
    # Przepis 4: Jeśli mamy sok lub napoje
    if any('sok' in n for n in product_names):
        juices = [item['nazwa'] for item in fridge_items if 'sok' in item['nazwa'].lower()]
        recipes.append({
            'title': 'Orzeźwiające smoothie',
            'ingredients_from_fridge': juices[:1],
            'ingredients_to_buy': ['Mrożone owoce (maliny, truskawki)', 'Miód'],
            'steps': [
                f'Do blendera wlej szklankę {juices[0] if juices else "soku"}',
                'Dodaj garść mrożonych owoców (ok. 100g)',
                'Dodaj łyżeczkę miodu',
                'Opcjonalnie dodaj kilka kostek lodu',
                'Miksuj 20-30 sekund do uzyskania gładkiej konsystencji',
                'Przelej do szklanek i podawaj od razu ze słomką'
            ],
            'calories_per_100g': 70
        })
    
    # Przepis 5: Jeśli mamy miód
    if any('miód' in n for n in product_names):
        recipes.append({
            'title': 'Rozgrzewająca herbata ziołowa z miodem',
            'ingredients_from_fridge': ['Miód'],
            'ingredients_to_buy': ['Herbata ziołowa (rumiankowa lub miętowa)', 'Cytryna'],
            'steps': [
                'Zagotuj szklankę wody w czajniku',
                'Zaparż torebkę herbaty ziołowej przez 5 minut',
                'Wyjmij torebkę i dodaj łyżeczkę miodu',
                'Dodaj plasterek cytryny',
                'Wymieszaj i pij na ciepło',
                'Idealnie rozgrzewa i wspomaga odporność'
            ],
            'calories_per_100g': 32
        })
    
    # Przepis 6: Uniwersalny przepis z mieszanką produktów
    if len(fridge_items) >= 3:
        mixed_items = [item['nazwa'] for item in fridge_items[:4]]
        recipes.append({
            'title': 'Zapiekanka z lodówki',
            'ingredients_from_fridge': mixed_items,
            'ingredients_to_buy': ['Ser żółty tarty', 'Bułka tarta', 'Masło'],
            'steps': [
                f'Pokrój w kostkę: {", ".join(mixed_items[:3])}',
                'Wysmaruj naczynie żaroodporne masłem',
                'Ułóż warstwami pokrojone składniki',
                'Każdą warstwę posyp tartym serem',
                'Wierzch posyp bułką tartą',
                'Piecz w 180°C przez 25-30 minut',
                'Podawaj na ciepło'
            ],
            'calories_per_100g': 185
        })
    
    # Dodaj informację o wymaganiach użytkownika jeśli były podane
    note = ""
    if user_message:
        note = f"\n\nUwaga: W trybie podstawowym nie mogę uwzględnić Twoich wymagań: '{user_message}'. Zainstaluj Ollama dla spersonalizowanych przepisów."
    
    # Ogranicz do wymaganej liczby
    recipes = recipes[:recipes_count]
    
    # Jeśli nie mamy wystarczająco przepisów, dodaj uniwersalny
    while len(recipes) < min(recipes_count, 2):
        recipes.append({
            'title': f'Posiłek #{len(recipes) + 1} z dostępnych produktów',
            'ingredients_from_fridge': [item['nazwa'] for item in fridge_items[:3]],
            'ingredients_to_buy': ['Przyprawy do smaku', 'Olej roślinny'],
            'steps': [
                'Przygotuj i umyj wszystkie składniki',
                'Pokrój je na odpowiednie kawałki',
                'Podgrzej patelnię z odrobiną oleju',
                'Smaż składniki około 10 minut',
                'Przypraw solą i pieprzem',
                'Podawaj na ciepło'
            ],
            'calories_per_100g': 120
        })
    
    return {
        'recipes': recipes
    }


@bp.route('/asystent-kucharza', methods=['GET'])
@jwt_required()
def chef_assistant_page():
    """
    Strona Asystenta Kucharza - interfejs chatowy z przepisami.
    Zabezpieczona logowaniem JWT.
    """
    try:
        user_id = get_jwt_identity()
        
        # Pobierz podstawowe info o produktach w lodówce
        fridge_items = get_user_fridge_items(user_id)
        products_count = len(fridge_items)
        
        return render_template(
            'chef_assistant.html',
            products_count=products_count
        )
        
    except Exception as e:
        flash(f'Błąd podczas ładowania asystenta kucharza: {str(e)}', 'error')
        return redirect(url_for('auth.dashboard'))


@bp.route('/kucharz', methods=['POST'])
@jwt_required()
def chef_assistant():
    """
    Endpoint AI Asystenta Kucharza.
    
    Pobiera produkty z lodówki użytkownika i generuje przepisy przy użyciu lokalnego AI (Ollama).
    
    Request JSON (opcjonalnie):
    {
        "user_message": "dodatkowe wymagania użytkownika"
    }
    
    Response JSON:
    {
        "success": true,
        "recipes_count": 4,
        "products_count": 6,
        "recipes": [
            {
                "title": "...",
                "ingredients_from_fridge": [...],
                "ingredients_to_buy": [...],
                "steps": [...],
                "calories_per_100g": 250
            }
        ]
    }
    """
    try:
        # Pobierz ID zalogowanego użytkownika
        user_id = get_jwt_identity()
        
        # Pobierz opcjonalną wiadomość użytkownika
        user_message = None
        if request.is_json and request.data:
            data = request.get_json()
            user_message = data.get('user_message') if data else None
        
        # Pobierz produkty z lodówki użytkownika
        fridge_items = get_user_fridge_items(user_id)
        
        if not fridge_items:
            return jsonify({
                'success': False,
                'message': 'Twoja lodówka jest pusta. Dodaj produkty, aby wygenerować przepisy.'
            }), 400
        
        # Oblicz liczbę przepisów
        products_count = len(fridge_items)
        recipes_count = calculate_recipes_count(products_count)
        
        if recipes_count == 0:
            return jsonify({
                'success': False,
                'message': 'Zbyt mało produktów w lodówce. Potrzebujesz co najmniej 2 produkty.'
            }), 400
        
        # Sprawdź czy Ollama jest dostępna
        ollama_available = check_ollama_availability()
        
        if ollama_available:
            # Zbuduj prompt dla AI
            prompt = build_ai_prompt(fridge_items, recipes_count, user_message)
            
            # Wywołaj Ollama API
            ai_result = call_ollama_api(prompt)
            
            if ai_result['success']:
                # Przygotuj odpowiedź z AI
                recipes_data = ai_result['data']
                
                return jsonify({
                    'success': True,
                    'recipes_count': recipes_count,
                    'products_count': products_count,
                    'fridge_items': [item['opis'] for item in fridge_items],
                    'recipes': recipes_data.get('recipes', []),
                    'ai_mode': 'ollama'
                })
        
        # Fallback: Użyj prostych przepisów gdy Ollama nie działa
        fallback_recipes = generate_fallback_recipes(fridge_items, recipes_count, user_message)
        
        # Dodaj komunikat o wymaganiach użytkownika jeśli były podane
        fallback_message = 'Ollama nie jest dostępna. Wyświetlam przykładowe przepisy. Aby uzyskać spersonalizowane przepisy AI, zainstaluj Ollama: https://ollama.com'
        if user_message:
            fallback_message += f'\n\nℹ️ W trybie podstawowym nie mogę uwzględnić Twoich wymagań: "{user_message}". Potrzebuję Ollama AI dla spersonalizowanych przepisów.'
        
        return jsonify({
            'success': True,
            'recipes_count': recipes_count,
            'products_count': products_count,
            'fridge_items': [item['opis'] for item in fridge_items],
            'recipes': fallback_recipes.get('recipes', []),
            'ai_mode': 'fallback',
            'message': fallback_message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd serwera: {str(e)}'
        }), 500
