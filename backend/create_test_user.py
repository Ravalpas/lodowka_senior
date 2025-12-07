"""
Skrypt do tworzenia testowego użytkownika
"""
from app import create_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Sprawdź czy użytkownik już istnieje
    existing_user = User.query.filter_by(email='test@test.pl').first()
    
    if existing_user:
        print(f"✅ Użytkownik test@test.pl już istnieje (ID: {existing_user.id})")
    else:
        # Stwórz nowego użytkownika
        new_user = User(
            email='test@test.pl',
            imie='Jan',
            nazwisko='Kowalski',
            haslo_hash=generate_password_hash('test123')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        print(f"✅ Utworzono użytkownika: test@test.pl (hasło: test123)")
        print(f"   ID: {new_user.id}")
        print(f"   Imię: {new_user.pelne_imie}")
    
    # Wyświetl wszystkich użytkowników
    print("\n📋 Wszyscy użytkownicy w bazie:")
    users = User.query.all()
    for user in users:
        print(f"   - {user.email} (ID: {user.id}, {user.pelne_imie})")
