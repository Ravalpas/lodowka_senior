from app import create_app
from app.models import FridgeItem

app = create_app()

with app.app_context():
    items = FridgeItem.query.filter(FridgeItem.usunieto.is_(None)).all()
    print(f"\nProdukty w lodowce: {len(items)}\n")
    
    for i in items[:10]:
        nazwa = i.nazwa_wlasna or "produkt"
        print(f"ID: {i.id}, Nazwa: {nazwa}, Ilosc: {i.ilosc} {i.jednostka_g_ml_szt}")
