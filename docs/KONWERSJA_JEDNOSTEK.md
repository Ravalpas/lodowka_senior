# Konwersja i Sumowanie Jednostek w Lodówce Senior+

## Przegląd

System automatycznie konwertuje i sumuje produkty o różnych jednostkach masy i objętości.

## Obsługiwane Jednostki

### Masa (Weight)
- **g** (gramy) - podstawowa jednostka
- **kg** (kilogramy) - 1 kg = 1000 g

### Objętość (Volume)
- **ml** (mililitry) - podstawowa jednostka
- **l** (litry) - 1 l = 1000 ml

### Sztuki (Pieces)
- **szt** (sztuki) - nie podlegają konwersji

## Jak Działa Sumowanie?

Produkty są sumowane gdy mają:
1. **Ten sam produkt** (produkt_id lub nazwa_wlasna)
2. **Tę samą datę ważności** (wazne_do)

System automatycznie konwertuje jednostki podczas sumowania:

### Przykład 1: Mięso
```
Pozycja 1: 200g Mięsa, ważne do: 2025-12-10
Pozycja 2: 1kg Mięsa, ważne do: 2025-12-10
---
WYNIK: 1.2 kg Mięsa (automatyczna konwersja)
```

### Przykład 2: Mleko
```
Pozycja 1: 500ml Mleka, ważne do: 2025-12-15
Pozycja 2: 1.5l Mleka, ważne do: 2025-12-15
---
WYNIK: 2 l Mleka (500ml + 1500ml = 2000ml → 2l)
```

### Przykład 3: Różne Daty Ważności
```
Pozycja 1: 300g Sera, ważne do: 2025-12-10
Pozycja 2: 400g Sera, ważne do: 2025-12-12
---
WYNIK: 
- 300 g Sera (ważne do 2025-12-10)
- 400 g Sera (ważne do 2025-12-12)
(NIE sumują się - różne daty)
```

## Inteligentne Wyświetlanie

System automatycznie wybiera najlepszą jednostkę do wyświetlenia:

### Masa
- **< 1000g** → wyświetla w gramach (np. 750 g)
- **≥ 1000g** → wyświetla w kilogramach (np. 1.5 kg)

### Objętość
- **< 1000ml** → wyświetla w mililitrach (np. 250 ml)
- **≥ 1000ml** → wyświetla w litrach (np. 1.25 l)

## Przykłady Użycia

### Scenariusz 1: Planowanie Posiłków
```
Dodaj: 500g mięsa mielonego (kg), ważne do: jutro
Dodaj: 300g mięsa mielonego (g), ważne do: jutro
---
System pokazuje: 0.8 kg mięsa mielonego
Idealne do przygotowania potraw dla całej rodziny!
```

### Scenariusz 2: Napoje
```
Dodaj: 1l soku pomarańczowego (l), ważne do: 2025-12-20
Dodaj: 500ml soku pomarańczowego (ml), ważne do: 2025-12-20
---
System pokazuje: 1.5 l soku pomarańczowego
```

### Scenariusz 3: Śmietana w Różnych Opakowaniach
```
Dodaj: 200ml śmietany 18% (ml), ważne do: 2025-12-08
Dodaj: 250ml śmietany 18% (ml), ważne do: 2025-12-08
Dodaj: 150ml śmietany 18% (ml), ważne do: 2025-12-08
---
System pokazuje: 600 ml śmietany 18%
(nie konwertuje do 0.6l, bo < 1000ml)
```

## Dodawanie Produktów

### W Formularzu:
1. Wybierz jednostkę odpowiednią dla opakowania:
   - Małe opakowania: g, ml
   - Duże opakowania: kg, l
   - Produkty liczone: szt

2. Wprowadź ilość według opakowania:
   - Jeśli masz 2 kg mięsa → wybierz "2" i "kg"
   - Jeśli masz 250g masła → wybierz "250" i "g"
   - Jeśli masz 1.5l mleka → wybierz "1.5" i "l"

## Zalety Systemu

✅ **Automatyczna konwersja** - nie musisz liczyć w głowie
✅ **Inteligentne grupowanie** - produkty sumują się automatycznie
✅ **Czytelne wyświetlanie** - zawsze w najlepszej jednostce
✅ **Elastyczność** - dodawaj produkty w dowolnych jednostkach
✅ **Dokładność** - precyzyjne sumowanie bez zaokrągleń

## Uwagi Techniczne

- Wewnętrznie system używa **miligramów (mg)** dla masy i **mikrolitów (µl)** dla objętości
- Dzięki temu sumowanie jest zawsze precyzyjne
- Konwersja odbywa się tylko podczas wyświetlania
- Dane w bazie przechowywane są w oryginalnych jednostkach
