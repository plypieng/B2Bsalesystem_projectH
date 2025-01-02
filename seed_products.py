# seed_products.py
from app import create_app
from models import db, Product

def seed_products():
    app = create_app()
    with app.app_context():
        # Example: Add or update each product
        items = [
            Product(name="1 Day Pass (Group)", category="voucher", default_price=750),
            Product(name="2 Day Pass (Group)", category="voucher", default_price=1300),
            Product(name="3 Day Pass (Group)", category="voucher", default_price=1800),
            Product(name="1 Day Pass (PV)", category="voucher", default_price=1390),
            Product(name="2 Day Pass (PV)", category="voucher", default_price=2500),
            Product(name="3 Day Pass (PV)", category="voucher", default_price=3450),
            Product(name="Activities Group (On-site, 10p)", category="activities_group", default_price=900),
            # ... etc. fill in for 15p, 20p, ...
            Product(name="Activities Group (Off-site, 20p)", category="activities_group", default_price=1300),
            # ...
            Product(name="B2BC Base", category="b2bc", default_price=0),
        ]

        for item in items:
            # check if product already in db
            existing = Product.query.filter_by(name=item.name).first()
            if existing:
                existing.default_price = item.default_price
                existing.category = item.category
            else:
                db.session.add(item)

        db.session.commit()
        print("Products seeded successfully.")

if __name__ == "__main__":
    seed_products()
