# Model użytkownika
# Reprezentuje użytkowników systemu (seniorów i opiekunów)

from ..extensions import db
from datetime import datetime


class User(db.Model):
    """
    Model użytkownika systemu Lodówka Senior+
    Odwzorowuje tabelę 'uzytkownicy' z bazy danych
    """
    __tablename__ = 'uzytkownicy'
    
    id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(190), unique=True, nullable=False, index=True)
    haslo_hash = db.Column(db.String(255), nullable=False)
    imie = db.Column(db.String(190), nullable=True)
    nazwisko = db.Column(db.String(190), nullable=True)
    rola = db.Column(db.String(32), nullable=False, default='uzytkownik')
    utworzono = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    zaktualizowano = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    usunieto = db.Column(db.DateTime, nullable=True)
    usunal_id = db.Column(db.BigInteger, nullable=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Konwertuje obiekt użytkownika na słownik (bez hasła)"""
        return {
            'id': self.id,
            'email': self.email,
            'imie': self.imie,
            'nazwisko': self.nazwisko,
            'rola': self.rola,
            'utworzono': self.utworzono.isoformat() if self.utworzono else None
        }
    
    @property
    def pelne_imie(self):
        """Zwraca pełne imię i nazwisko lub email jeśli brak"""
        if self.imie and self.nazwisko:
            return f"{self.imie} {self.nazwisko}"
        elif self.imie:
            return self.imie
        return self.email
