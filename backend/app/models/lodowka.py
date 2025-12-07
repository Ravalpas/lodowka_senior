# backend/app/models/lodowka.py
# Model lodówki – odwzorowanie tabeli "lodowka"

from datetime import datetime
from ..extensions import db


class Lodowka(db.Model):
    __tablename__ = "lodowka"

    id = db.Column(db.BigInteger, primary_key=True)
    nazwa = db.Column(db.String(190), nullable=False, default="Moja lodowka")
    wlasciciel_id = db.Column(
        db.BigInteger, db.ForeignKey("uzytkownicy.id"), nullable=False
    )
    utworzono = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    zaktualizowano = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    usunieto = db.Column(db.DateTime, nullable=True)
    usunal_id = db.Column(db.BigInteger, db.ForeignKey("uzytkownicy.id"), nullable=True)

    # Relacje
    wlasciciel = db.relationship("User", foreign_keys=[wlasciciel_id], backref="lodowki")

    def __repr__(self) -> str:
        return f"<Lodowka id={self.id} nazwa={self.nazwa!r} wlasciciel_id={self.wlasciciel_id}>"
