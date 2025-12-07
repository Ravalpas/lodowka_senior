from datetime import datetime

from ..extensions import db


class OperationHistory(db.Model):
    """
    Mapuje tabelę `historia_operacji_pozycji`.

    Dziennik: co zostało dodane/zużyte/usunięte z danej pozycji w lodówce.
    """
    __tablename__ = "historia_operacji_pozycji"

    id = db.Column(db.BigInteger, primary_key=True)  # PK, AUTO_INCREMENT
    pozycja_id = db.Column(
        db.BigInteger,
        db.ForeignKey("magazyn_pozycje_lodowki.id"),
        nullable=False,
    )
    typ = db.Column(db.String(16), nullable=False)  # 'dodano' / 'zuzyto' / 'usunieto'
    ilosc = db.Column(db.Numeric(10, 3), nullable=False)
    jednostka_g_ml_szt = db.Column(db.String(8), nullable=False)
    komentarz = db.Column(db.String(255))
    uzytkownik_id = db.Column(
        db.BigInteger,
        db.ForeignKey("uzytkownicy.id"),
        nullable=True,
    )
    utworzono = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.func.current_timestamp(),
    )

    # Relacje (opcjonalne, ale przydatne później)
    pozycja = db.relationship(
        "FridgeItem",
        backref=db.backref("historia_operacji", lazy="dynamic"),
        foreign_keys=[pozycja_id],
    )
    uzytkownik = db.relationship("User", foreign_keys=[uzytkownik_id])

    def __repr__(self) -> str:
        return (
            f"<OperationHistory id={self.id} "
            f"pozycja_id={self.pozycja_id} typ={self.typ} "
            f"ilosc={self.ilosc} {self.jednostka_g_ml_szt}>"
        )
