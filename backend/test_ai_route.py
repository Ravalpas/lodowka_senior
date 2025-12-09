# Test skryptu do sprawdzenia czy endpoint AI działa

from app import create_app
from app.extensions import db
from app.models import User, Lodowka

app = create_app()

with app.app_context():
    # Znajdź pierwszego użytkownika
    user = User.query.first()
    if user:
        print(f"User found: {user.email}, ID: {user.id}")
        
        # Sprawdź czy ma lodówkę
        lodowka = Lodowka.query.filter_by(wlasciciel_id=user.id).first()
        if lodowka:
            print(f"Lodowka found: ID={lodowka.id}")
        else:
            print("No lodowka for this user")
            # Pokaż wszystkie lodówki
            wszystkie = Lodowka.query.all()
            print(f"All lodowki: {[(l.id, l.wlasciciel_id) for l in wszystkie]}")
        
        # Import tutaj żeby app context był gotowy
        from app.routes.ai import get_user_fridge_items
        
        # Testuj funkcję
        try:
            fridge_items = get_user_fridge_items(user.id)
            print(f"Fridge items: {len(fridge_items)}")
            for item in fridge_items:
                print(f"  - {item['opis']}")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No user found")
