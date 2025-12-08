from app import create_app
from app.models import FridgeItem, Product, WartosciOdzywcze

app = create_app()

with app.app_context():
    items = FridgeItem.query.filter(FridgeItem.usunieto.is_(None)).all()
    print(f"\nProdukty w lodówce: {len(items)}\n")
    
    for item in items:
        print(f"\nID: {item.id}")
        print(f"  nazwa_wlasna: {item.nazwa_wlasna}")
        print(f"  produkt_id: {item.produkt_id}")
        
        if item.produkt_id:
            product = Product.query.get(item.produkt_id)
            if product:
                print(f"  → Produkt: {product.nazwa}")
                print(f"     Marka: {product.marka}")
                print(f"     Kod: {product.barcode_13cyf}")
                
                wartosci = WartosciOdzywcze.query.filter_by(produkt_id=product.id).first()
                if wartosci:
                    print(f"     Wartości odżywcze: TAK (kcal: {wartosci.na_100g_kcal})")
                else:
                    print(f"     Wartości odżywcze: BRAK")
            else:
                print(f"  → BŁĄD: produkt_id={item.produkt_id} nie istnieje!")
        else:
            print(f"  → Brak powiązania z tabelą produkty")
