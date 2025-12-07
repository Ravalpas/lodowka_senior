# backend/app/models/fridge_item.py
# Model pozycji w lodówce – odwzorowanie tabeli "magazyn_pozycje_lodowki"

from datetime import datetime
from ..extensions import db


class FridgeItem(db.Model):
    __tablename__ = "magazyn_pozycje_lodowki"  # dokładna nazwa tabeli w MySQL

    # klucz główny
    id = db.Column(db.BigInteger, primary_key=True)

    # powiązania z innymi tabelami
    lodowka_id = db.Column(db.BigInteger, db.ForeignKey("lodowka.id"), nullable=False)
    produkt_id = db.Column(db.BigInteger, db.ForeignKey("produkty.id"), nullable=True)

    # dane użytkownika, który dodał / usunął
    dodal_uzytkownik_id = db.Column(
        db.BigInteger, db.ForeignKey("uzytkownicy.id"), nullable=True
    )
    usunal_id = db.Column(db.BigInteger, db.ForeignKey("uzytkownicy.id"), nullable=True)

    # nazwa własna produktu w lodówce (np. „Jogurt naturalny 150g”)
    nazwa_wlasna = db.Column(db.String(190), nullable=True)

    # ilość i jednostka
    ilosc = db.Column(db.Numeric(10, 3), nullable=False, default=0)
    jednostka_g_ml_szt = db.Column(db.String(8), nullable=False, default="g")

    # data ważności i sposób dodania
    wazne_do = db.Column(db.Date, nullable=True)
    jak_dodano_pozycje = db.Column(db.String(16), nullable=False, default="manual")

    # wartości odżywcze dla tej pozycji (opcjonalne)
    kcal = db.Column(db.Numeric(10, 3), nullable=True)
    bialko_g = db.Column(db.Numeric(10, 3), nullable=True)
    tluszcz_g = db.Column(db.Numeric(10, 3), nullable=True)
    weglowodany_g = db.Column(db.Numeric(10, 3), nullable=True)

    # metadane czasowe
    utworzono = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    zaktualizowano = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    usunieto = db.Column(db.DateTime, nullable=True)

    # relacje – na razie tylko do istniejących klas (Product, User),
    # NIE odwołujemy się jeszcze do klasy Lodowka (bo jej nie ma).
    produkt = db.relationship("Product", backref="pozycje_lodowki", lazy="joined")
    dodal_uzytkownik = db.relationship(
        "User",
        foreign_keys=[dodal_uzytkownik_id],
        backref="dodane_pozycje_lodowki",
        lazy="joined",
    )
    usunal_uzytkownik = db.relationship(
        "User",
        foreign_keys=[usunal_id],
        backref="usuniete_pozycje_lodowki",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<FridgeItem id={self.id} nazwa={self.nazwa_wlasna!r} ilosc={self.ilosc} {self.jednostka_g_ml_szt}>"
