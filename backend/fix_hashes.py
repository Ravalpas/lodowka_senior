"""Naprawia hashy użytkowników do jednego, aktualnego formatu"""
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import User
from app.extensions import db

app = create_app()

# Mapowanie użytkownik -> nowe hasło (dla testowych kont)
test_passwords = {
    'test@example.com': 'test123',
    'test@loql': 'test123', 
    'ravalpas@wp.pl': 'test123',
    'test@test.pl': 'test123'
}

with app.app_context():
    print("\n=== Aktualizacja hashy użytkowników ===\n")
    
    updated = 0
    for email, password in test_passwords.items():
        user = User.query.filter_by(email=email).first()
        if user:
            # Wygeneruj nowy hash (bez deprecated parametru method)
            new_hash = generate_password_hash(password)
            user.haslo_hash = new_hash
            
            print(f"✓ {email}")
            print(f"  Stary format: {user.haslo_hash[:20]}...")
            print(f"  Nowy format: {new_hash[:60]}...")
            print(f"  Hasło: {password}")
            print()
            updated += 1
    
    if updated > 0:
        try:
            db.session.commit()
            print(f"\n✓ Zaktualizowano {updated} użytkowników")
            print("Wszystkie konta mają teraz hasło: test123")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Błąd: {e}")
    else:
        print("Nie znaleziono użytkowników do aktualizacji")
