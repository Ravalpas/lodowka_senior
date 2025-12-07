from app import create_app
from app.models import User
from app.extensions import db

app = create_app()

with app.app_context():
    users = User.query.all()
    print(f"\n=== Znaleziono {len(users)} użytkowników ===\n")
    
    for user in users:
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Hash: {user.haslo_hash[:50]}..." if len(user.haslo_hash) > 50 else f"Hash: {user.haslo_hash}")
        print(f"Hash starts with: {user.haslo_hash.split(':')[0] if ':' in user.haslo_hash else 'NO COLON'}")
        print("-" * 50)
