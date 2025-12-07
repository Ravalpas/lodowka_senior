"""Sprawdza formaty hashy użytkowników w bazie danych"""
from app import create_app
from app.models import User
from app.extensions import db

app = create_app()

with app.app_context():
    users = User.query.all()
    print(f"\n=== Znaleziono {len(users)} użytkowników ===\n")
    
    for user in users:
        hash_preview = user.haslo_hash[:60] if user.haslo_hash else "BRAK"
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Hash: {hash_preview}...")
        print(f"Długość: {len(user.haslo_hash) if user.haslo_hash else 0}")
        print("-" * 70)
