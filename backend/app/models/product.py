# backend/app/models/product.py
# Model słownika produktów – odwzorowanie tabeli "produkty" z bazy MySQL

from ..extensions import db


class Product(db.Model):
    __tablename__ = "produkty"  # dokładna nazwa tabeli z bazy

    id = db.Column(db.BigInteger, primary_key=True)  # klucz główny

    # poniższe pola odwzorowują najważniejsze kolumny z tabeli "produkty"
    nazwa = db.Column(db.String(190), nullable=False)
    marka = db.Column(db.String(128))
    kategoria = db.Column(db.String(64))
    barcode_13cyf = db.Column(db.String(32))

    # jednostka: 'g', 'ml' lub 'szt'
    domyslna_jednostka_g_ml_szt = db.Column(db.String(8), nullable=False, default="g")

    # ile gramów ma 1 sztuka (może być NULL)
    gramow_na_szt = db.Column(db.Numeric(10, 3))

    utworzono = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    zaktualizowano = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    usunieto = db.Column(db.DateTime, nullable=True)
    usunal_id = db.Column(db.BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<Product id={self.id} nazwa={self.nazwa!r}>"
