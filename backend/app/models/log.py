from datetime import datetime
from ..extensions import db


class Log(db.Model):
    __tablename__ = "logi_zdarzen"

    id = db.Column(db.BigInteger, primary_key=True)

    typ = db.Column(db.String(32), nullable=False)
    tabela = db.Column(db.String(64), nullable=False)
    rekord_id = db.Column(db.BigInteger, nullable=False)

    uzytkownik_id = db.Column(
        db.BigInteger,
        db.ForeignKey("uzytkownicy.id"),
        nullable=True,
    )
    lodowka_id = db.Column(db.BigInteger, nullable=True)

    czas = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.func.current_timestamp(),
    )

    przed = db.Column(db.Text)
    po = db.Column(db.Text)

    uzytkownik = db.relationship("User", foreign_keys=[uzytkownik_id])

    def __repr__(self) -> str:
        return (
            f"<Log id={self.id} typ={self.typ} "
            f"tabela={self.tabela} rekord_id={self.rekord_id}>"
        )
