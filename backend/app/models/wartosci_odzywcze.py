# backend/app/models/wartosci_odzywcze.py
# Model wartości odżywczych produktów - odwzorowanie tabeli "wartosci_odzywcze"

from ..extensions import db


class WartosciOdzywcze(db.Model):
    __tablename__ = "wartosci_odzywcze"

    id = db.Column(db.BigInteger, primary_key=True)
    produkt_id = db.Column(db.BigInteger, db.ForeignKey('produkty.id'), nullable=False)
    cache_id = db.Column(db.Integer, nullable=True)
    zrodlo_id = db.Column(db.BigInteger, nullable=True)
    
    # Wartości odżywcze na 100g
    na_100g_kcal = db.Column(db.Numeric(10, 3), nullable=True)
    na_100g_bialko_g = db.Column(db.Numeric(10, 3), nullable=True)
    na_100g_tluszcz_g = db.Column(db.Numeric(10, 3), nullable=True)
    na_100g_weglowodany_g = db.Column(db.Numeric(10, 3), nullable=True)
    na_100g_blonnik_g = db.Column(db.Numeric(10, 3), nullable=True)
    na_100g_sol_g = db.Column(db.Numeric(10, 3), nullable=True)
    
    # Pełne dane JSON z API
    odp_api = db.Column(db.JSON, nullable=True)
    api = db.Column(db.JSON, nullable=True)
    
    pobrano = db.Column(db.DateTime, nullable=True)
    zaktualizowano = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    
    # Relacja do produktu
    produkt = db.relationship('Product', backref=db.backref('wartosci_odzywcze', lazy=True))

    def __repr__(self) -> str:
        return f"<WartosciOdzywcze produkt_id={self.produkt_id} kcal={self.na_100g_kcal}>"
