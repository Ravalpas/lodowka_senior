# Serwis autentykacji
# Logika biznesowa związana z autentykacją i autoryzacją użytkowników

from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from ..models import User
from ..extensions import db


class AuthService:
    """
    Serwis obsługujący autentykację użytkowników.
    """

    @staticmethod
    def register_user(email, password, password_confirm, imie=None, nazwisko=None, rola: str = "uzytkownik"):
        """
        Rejestruje nowego użytkownika.

        Args:
            email: Adres email.
            password: Hasło (plain text - zostanie zahashowane).
            password_confirm: Potwierdzenie hasła.
            imie: Imię użytkownika (opcjonalne).
            nazwisko: Nazwisko użytkownika (opcjonalne).
            rola: Rola użytkownika (domyślnie 'uzytkownik').

        Returns:
            Obiekt User w przypadku sukcesu.

        Raises:
            ValueError: Gdy dane są nieprawidłowe lub wystąpił błąd zapisu.
        """
        # Walidacja email
        if not email or "@" not in email:
            raise ValueError("Nieprawidłowy adres email")

        # Walidacja hasła
        if not password or len(password) < 6:
            raise ValueError("Hasło musi mieć minimum 6 znaków")

        if password != password_confirm:
            raise ValueError("Hasła nie są identyczne")

        # Sprawdzenie unikalności email
        existing_user = User.query.filter_by(email=email.lower().strip()).first()
        if existing_user:
            raise ValueError("Użytkownik z tym adresem email już istnieje")

        # Hashowanie hasła
        haslo_hash = generate_password_hash(password)

        # Utworzenie nowego użytkownika
        now = datetime.utcnow()
        new_user = User(
            email=email.lower().strip(),
            haslo_hash=haslo_hash,
            imie=imie.strip() if imie else None,
            nazwisko=nazwisko.strip() if nazwisko else None,
            rola=rola,
            utworzono=now,
            zaktualizowano=now,
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            return new_user
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Błąd podczas rejestracji: {str(e)}")

    @staticmethod
    def authenticate_user(email: str, password: str):
        """
        Uwierzytelnia użytkownika.

        Args:
            email: Adres email.
            password: Hasło.

        Returns:
            dict z tokenem JWT i danymi użytkownika lub None,
            jeśli uwierzytelnienie się nie powiodło.
        """
        if not email or not password:
            return None

        # Znajdź użytkownika
        user = User.query.filter_by(email=email.lower().strip()).first()

        # Sprawdź czy użytkownik istnieje i nie jest usunięty
        if not user or user.usunieto is not None:
            return None

        # Weryfikacja hasła
        try:
            if not check_password_hash(user.haslo_hash, password):
                return None
        except Exception:
            # Hash w bazie jest w nieprawidłowym formacie - zwróć None (nieprawidłowe hasło)
            return None

        # Generowanie tokenu JWT
        # JWT wymaga, żeby "sub" (identity) był stringiem,
        # dlatego rzutujemy id użytkownika na str.
        access_token = create_access_token(identity=str(user.id))

        return {
            "access_token": access_token,
            "user": user.to_dict(),
        }

    @staticmethod
    def get_user_by_id(user_id):
        """
        Pobiera użytkownika po ID.

        Args:
            user_id: ID użytkownika (int lub str).

        Returns:
            Obiekt User lub None.
        """
        return User.query.filter_by(id=user_id, usunieto=None).first()

    @staticmethod
    def change_password(user_id, old_password: str, new_password: str):
        """
        Zmienia hasło użytkownika.

        Args:
            user_id: ID użytkownika.
            old_password: Stare hasło.
            new_password: Nowe hasło.

        Returns:
            True jeśli hasło zostało zmienione, False w przeciwnym wypadku.
        """
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return False

        # Weryfikacja starego hasła
        if not check_password_hash(user.haslo_hash, old_password):
            return False

        # Walidacja nowego hasła
        if len(new_password) < 6:
            raise ValueError("Nowe hasło musi mieć minimum 6 znaków")

        # Hashowanie nowego hasła
        user.haslo_hash = generate_password_hash(new_password, method="pbkdf2:sha256")
        user.zaktualizowano = datetime.utcnow()

        try:
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
