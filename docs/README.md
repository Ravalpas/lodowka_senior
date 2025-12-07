# Lodówka Senior+ 🥬🍎

Aplikacja do zarządzania produktami w lodówce dla seniorów i ich opiekunów.

## Opis projektu

**Lodówka Senior+** to system webowy wspierający seniorów w zarządzaniu zawartością lodówki. Aplikacja pomaga:
- Śledzić daty ważności produktów
- Otrzymywać powiadomienia o produktach zbliżających się do przeterminowania
- Prowadzić historię operacji na produktach
- Monitorować statystyki dotyczące marnotrawstwa żywności

## Architektura

### Backend
- **Framework**: Flask (Python)
- **Baza danych**: MySQL
- **Autentykacja**: JWT (Flask-JWT-Extended)
- **ORM**: SQLAlchemy

### Frontend
- **HTML5** z szablonami Jinja2
- **Tailwind CSS** do stylizacji
- **Vanilla JavaScript** do komunikacji z API

## Struktura projektu

```
lodowka_senior/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Factory aplikacji Flask
│   │   ├── config.py            # Konfiguracja (dev, prod, test)
│   │   ├── extensions.py        # Rozszerzenia (SQLAlchemy, JWT)
│   │   ├── models/              # Modele bazy danych
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── fridge_item.py
│   │   │   ├── operation_history.py
│   │   │   └── log.py
│   │   ├── routes/              # Blueprinty Flask (endpoints)
│   │   │   ├── auth.py          # Autentykacja
│   │   │   ├── fridge.py        # Zarządzanie lodówką
│   │   │   ├── history.py       # Historia operacji
│   │   │   └── logs.py          # Logi systemowe
│   │   ├── services/            # Logika biznesowa
│   │   │   ├── auth_service.py
│   │   │   ├── fridge_service.py
│   │   │   ├── product_service.py
│   │   │   └── notification_service.py
│   │   ├── templates/           # Szablony HTML
│   │   │   ├── base.html
│   │   │   ├── login.html
│   │   │   ├── dashboard.html
│   │   │   ├── fridge.html
│   │   │   ├── expiring.html
│   │   │   ├── history.html
│   │   │   └── logs.html
│   │   └── static/              # Zasoby statyczne
│   │       ├── css/
│   │       │   ├── input.css    # Tailwind input
│   │       │   └── styles.css   # Skompilowany CSS
│   │       ├── js/
│   │       │   ├── main.js      # Główne funkcje
│   │       │   └── fridge.js    # Logika zarządzania lodówką
│   │       └── img/             # Obrazy
│   ├── tests/                   # Testy jednostkowe
│   ├── requirements.txt         # Zależności Pythona
│   └── run.py                   # Punkt wejścia aplikacji
└── docs/                        # Dokumentacja
    └── README.md                # Ten plik
```

## Funkcjonalności (planowane)

### Dla użytkowników
- ✅ Logowanie i zarządzanie kontem
- ✅ Dodawanie produktów do lodówki
- ✅ Edycja i usuwanie produktów
- ✅ Przeglądanie produktów wygasających
- ✅ Historia operacji
- ✅ Dashboard z statystykami

### Dla administratorów
- ✅ Przeglądanie logów systemowych
- ✅ Zarządzanie słownikiem produktów

## Instalacja i uruchomienie

### Wymagania
- Python 3.9+
- MySQL 8.0+
- Node.js (do kompilacji Tailwind CSS)

### Kroki instalacji

1. **Klonowanie repozytorium**
```bash
cd lodowka_senior
```

2. **Utworzenie środowiska wirtualnego**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

3. **Instalacja zależności**
```bash
cd backend
pip install -r requirements.txt
```

4. **Konfiguracja bazy danych**
- Utwórz bazę danych MySQL
- Skonfiguruj zmienne środowiskowe lub edytuj `backend/app/config.py`:
  - `MYSQL_HOST`
  - `MYSQL_USER`
  - `MYSQL_PASSWORD`
  - `MYSQL_DB`

5. **Kompilacja Tailwind CSS** (opcjonalne na tym etapie)
```bash
# TODO: Dodać instrukcje po skonfigurowaniu Tailwind
```

6. **Uruchomienie aplikacji**
```bash
cd backend
python run.py
```

Aplikacja będzie dostępna pod adresem: `http://localhost:5000`

## Rozwój

### TODO - Najbliższe kroki
- [ ] Implementacja struktury bazy danych (plik SQL)
- [ ] Implementacja modeli SQLAlchemy
- [ ] Implementacja endpointów API
- [ ] Implementacja logiki biznesowej w serwisach
- [ ] Stworzenie frontendowych formularzy i widoków
- [ ] Konfiguracja Tailwind CSS
- [ ] Implementacja systemu powiadomień
- [ ] Testy jednostkowe i integracyjne
- [ ] Dokumentacja API

## Licencja

TODO: Dodać informacje o licencji

## Autorzy

TODO: Dodać informacje o autorach

---

*Projekt w fazie rozwoju - ostatnia aktualizacja: 2025-12-06*

# Lodówka Senior+ (wersja Flask + HTML + Tailwind)

Nowa wersja aplikacji **Lodówka Senior+** – systemu do pilnowania terminów ważności produktów spożywczych dla osób starszych (i nie tylko).  
W tej wersji backend jest napisany w **Pythonie (Flask)**, a frontend w **czystym HTML + Tailwind CSS + JavaScript**, bez frameworków typu React.

---

## 1. Cel projektu

Aplikacja ma pomagać użytkownikowi:

- zapisywać produkty znajdujące się w lodówce,
- śledzić **ilość**, **jednostkę** (szt, g, ml) i **datę ważności**,
- pokazywać produkty, których termin ważności się zbliża lub już minął,
- prowadzić **historię operacji** (dodania, zużycia, wyrzucenia),
- zapamiętywać **logi zdarzeń**,
- umożliwiać wygodne zarządzanie produktami z prostego interfejsu (przystępnego także dla seniorów).

Schemat bazy danych jest dostarczony osobno w pliku SQL i **nie jest modyfikowany** – backend jedynie korzysta z istniejącej struktury (np. tabele `uzytkownicy`, `magazyn_pozycje_lodowki`, `historia_operacji_pozycji`, `logi_zdarzen`, `produkty`, `wartosci_odzywcze` itd.).

---

## 2. Stos technologiczny

### Backend

- **Język:** Python 3.x  
- **Framework:** Flask
- **Baza danych:** MySQL (istniejący schemat z pliku `baza.sql`)
- **Warstwa dostępu do danych:** SQLAlchemy lub klasyczne zapytania SQL (do ustalenia w trakcie implementacji – preferowany SQLAlchemy)
- **Uwierzytelnianie:** JWT (JSON Web Token) lub sesje cookies (preferowane JWT, aby uprościć komunikację z frontendem)
- **Struktura API:** REST-owe endpointy dla operacji na:
  - użytkownikach (logowanie, rejestracja – jeśli będzie),
  - pozycjach lodówki,
  - produktach kończących się,
  - historii operacji,
  - logach zdarzeń.

### Frontend

- **HTML5** – statyczne widoki (layout panelu, formularze, tabele)
- **Tailwind CSS** – jako główny framework CSS (minimalizacja ręcznego pisania styli)
- **JavaScript (ES6)** – logika po stronie klienta:
  - wysyłanie requestów do API,
  - obsługa logowania i przechowywania tokenu,
  - renderowanie danych (lista produktów, historia itd.),
  - proste interakcje (formularze, przyciski, filtrowanie).
- **Assety** (obrazy/ikony) – wykorzystywane w interfejsie (np. logo, tła, ikonki produktów).

### Inne

- **Narzędzie developerskie:** Visual Studio Code + rozszerzenia AI (np. Copilot / ChatGPT / GitHub Models)
- **Kontrola wersji:** Git + GitHub
- **Środowisko uruchomieniowe:** lokalnie (np. `venv`), docelowo łatwe do wdrożenia na serwerze obsługującym Pythona i MySQL.

---

## 3. Ogólna architektura

Projekt będzie podzielony logicznie na dwie główne części:

1. **Backend (Flask)**  
   - Udostępnia REST API (endpointy zwracające JSON) dla frontendu.  
   - Odpowiada za:
     - logowanie użytkownika i generowanie tokenu,
     - odczyt i zapis danych w bazie,
     - walidację danych wejściowych,
     - podstawową logikę biznesową (sumowanie produktów, filtrowanie po dacie ważności itd.).

2. **Frontend (HTML + Tailwind + JS)**  
   - Może być serwowany statycznie przez Flask (np. z katalogu `templates` i `static`).  
   - Wykorzystuje JavaScript do komunikacji z API (fetch / XMLHttpRequest).  
   - Odpowiada za:
     - interfejs logowania,
     - ekran główny (dashboard),
     - widok „Moja lodówka”,
     - widok „Produkty kończące się”,
     - widok „Historia operacji”,
     - widok „Logi zdarzeń”.

Dane przepływają w prosty sposób:

> Użytkownik (przeglądarka) → Frontend (JS) → API Flask → Baza MySQL  
> Baza MySQL → API Flask → JSON → Frontend (JS) → widok HTML dla użytkownika

---

## 4. Funkcjonalności (wysoki poziom)

### 4.1. Uwierzytelnianie i autoryzacja

- Logowanie użytkownika (`email`, `hasło`) na podstawie tabeli `uzytkownicy`
  - weryfikacja hasła (hash w bazie),
  - generowanie tokenu (JWT) lub sesji,
  - zwrot podstawowych danych o użytkowniku (np. `id`, `rola`).
- (Opcjonalnie) Rejestracja nowego użytkownika – do ustalenia.

### 4.2. Dashboard

Po zalogowaniu użytkownik trafia na stronę główną panelu, z której ma dostęp do:

- **Moja lodówka** – lista wszystkich produktów,
- **Produkty kończące się** – ważne do dzisiaj / jutra / po terminie,
- **Wyszukaj produkt (API)** – połączenie z zewnętrznym API (np. Open Food Facts),
- **Przepisy** – opcjonalny moduł przepisów i proponowanych potraw,
- **Historia operacji** – wszystkie działania na pozycjach lodówki,
- **Logi zdarzeń** – bardziej techniczne logi dla zaawansowanego użytkownika.

### 4.3. Moja lodówka

- Dodawanie produktu (ręcznie lub z użyciem kodu kreskowego):
  - nazwa / nazwa własna,
  - jednostka: szt / g / ml,
  - ilość,
  - data ważności.
- Zużywanie produktu (np. „Zużyj 1 szt / 50 g”).  
- Wyrzucanie / usuwanie produktu z lodówki.
- Grupowanie i sumowanie pozycji:
  - produkty o tej samej nazwie, jednostce i dacie ważności mogą być sumowane (np. „Jogurt naturalny – 3 × 150 g”).

### 4.4. Produkty kończące się

- Lista produktów, których data „ważne do”:
  - minęła,
  - jest dzisiaj,
  - będzie jutro.
- Informacja, ile dni zostało do końca terminu (może być wartość ujemna).  
- Możliwość szybkiego „wyrzucenia” produktu, co od razu aktualizuje stan lodówki.

### 4.5. Historia operacji

- Lista operacji z tabeli `historia_operacji_pozycji`:
  - dodanie,
  - zużycie,
  - usunięcie / wyrzucenie,
  - zmiany ilości.
- Szczegóły:
  - czas operacji,
  - typ,
  - nazwa produktu,
  - ilość i jednostka,
  - (opcjonalnie) komentarz.

### 4.6. Logi zdarzeń

- Dane z tabeli `logi_zdarzen` (jeśli są):  
  - typ zdarzenia,
  - nazwa tabeli i rekord ID,
  - użytkownik / lodówka,
  - data, stan przed/po (np. w formie JSON).

---

## 5. Plan pracy z asystentem AI w VS Code

1. **Przygotowanie kontekstu**:
   - Umieszczenie w projekcie:
     - pliku `docs/baza.sql` z pełnym schematem bazy,
     - tego pliku `README.md`,
     - opcjonalnie szkicu widoków (np. wireframes).
2. **Zbudowanie podstaw backendu (Flask)** z pomocą asystenta:
   - konfiguracja połączenia z MySQL,
   - modele danych / warstwa dostępu do bazy,
   - endpointy do logowania i podstawowego pobierania danych.
3. **Dodanie uwierzytelniania (auth)**:
   - logowanie, walidacja hasła, generowanie tokenu,
   - middleware / dekorator sprawdzający token.
4. **Stworzenie prostego dashboardu HTML + Tailwind**:
   - layout panelu z menu,
   - podłączone żądania JS do istniejących endpointów.
5. **Rozbudowa funkcjonalności krok po kroku**:
   - Moja lodówka: dodawanie, wyświetlanie, zużywanie, usuwanie,
   - Produkty kończące się,
   - Historia operacji,
   - Logi zdarzeń,
   - integracja z zewnętrznym API (np. Open Food Facts).

Na każdym etapie asystent AI będzie korzystał z:

- schematu bazy (plik SQL),
- niniejszego README (założenia projektu),
- istniejącego kodu.

---

## 6. Założenia niefunkcjonalne

- **Bezpieczeństwo** – hasła nigdy nie są przechowywane w formie jawnej (hash + salt w bazie).  
- **Brak zmian w strukturze bazy** – projekt korzysta z istniejącego schematu.
- **Czytelność kodu** – oddzielenie warstwy prezentacji (HTML+Tailwind) od logiki biznesowej (Flask).
- **Prostota obsługi dla użytkownika** – najważniejsze operacje maksymalnie uproszczone, bez zbędnych kliknięć.
