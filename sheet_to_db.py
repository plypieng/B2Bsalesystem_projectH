# sheet_to_db.py
import gspread
from google.oauth2.service_account import Credentials
from app import create_app
from models import db, SalesVoucherGroup, SalesB2BC, Booking, Branch, User
import datetime
from flask import flash

def get_worksheet(sheet_name, worksheet_title):
    """
    Returns a gspread worksheet object given a sheet name and a worksheet title.
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file("path/to/your_service_account.json", scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name)
    return sheet.worksheet(worksheet_title)

def migrate_p2v_to_db():
    # Example: read the "P2V" tab in your spreadsheet
    ws = get_worksheet("ProjectH_Sales", "P2V")
    data = ws.get_all_records()
    
    for row in data:
        sale_date_str = row.get("Sale Date")
        sale_date = datetime.datetime.strptime(sale_date_str, '%Y-%m-%d') if sale_date_str else datetime.datetime.utcnow()
        
        product_name = row.get("Voucher Type")
        quantity = row.get("Quantity Sold", 1)
        price_per_unit = float(row.get("Price (Per Unit)", 0))
        total_price = float(row.get("Total Price", 0))
        vat_7 = float(row.get("Vat 7%", 0))
        total_sale = float(row.get("Total Sale", 0))
        partner_name = row.get("Partner Name", "")
        branch_name = row.get("Branch Name", "Default Branch")
        
        # Ensure branch exists
        branch = Branch.query.filter_by(name=branch_name).first()
        if not branch:
            branch = Branch(name=branch_name, location="Unknown Location")
            db.session.add(branch)
            db.session.commit()
        
        sale = SalesVoucherGroup(
            sale_date=sale_date,
            sale_type="voucher",
            product_name=product_name,
            quantity=int(quantity),
            price_per_unit=price_per_unit,
            total_price=total_price,
            vat_7=vat_7,
            total_sale=total_sale,
            partner_name=partner_name,
            branch_id=branch.id,
            noted=row.get("Notes", "")
        )
        db.session.add(sale)
        
        # If there's a booking date, create a booking
        booking_date_str = row.get("Booking Date")
        if booking_date_str:
            booking_date = datetime.datetime.strptime(booking_date_str, '%Y-%m-%d').date()
            time_slot = row.get("Time", "")
            booking = Booking(
                voucher_group_sale_id=sale.id,
                booking_date=booking_date,
                time_slot=time_slot,
                status='booked',
                branch_id=branch.id,
                noted=row.get("Booking Notes", "")
            )
            db.session.add(booking)
    
    db.session.commit()

def migrate_b2bc_to_db():
    # Read the "B2BC" tab
    ws = get_worksheet("ProjectH_Sales", "B2BC")
    data = ws.get_all_records()

    for row in data:
        sale_date_str = row.get("Sale Date")
        sale_date = datetime.datetime.strptime(sale_date_str, '%Y-%m-%d') if sale_date_str else datetime.datetime.utcnow()
        
        course_name = row.get("Course Name", "Muay Thai Course")
        price = float(row.get("Price", 0))
        commission_rate = float(row.get("Commission Rate", 0.1))
        commission_amount = price * commission_rate
        branch_name = row.get("Branch Name", "Default Branch")
        
        # Ensure branch exists
        branch = Branch.query.filter_by(name=branch_name).first()
        if not branch:
            branch = Branch(name=branch_name, location="Unknown Location")
            db.session.add(branch)
            db.session.commit()
        
        # Ensure the salesperson exists
        salesperson_username = row.get("Salesperson", "admin")
        salesperson = User.query.filter_by(username=salesperson_username).first()
        if not salesperson:
            salesperson = User(username='admin', email='admin@example.com', role='admin', branch_id=branch.id)
            salesperson.set_password('adminpassword')
            db.session.add(salesperson)
            db.session.commit()
        
        sale = SalesB2BC(
            sale_date=sale_date,
            course_name=course_name,
            price=price,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            user_id=salesperson.id,
            branch_id=branch.id,
            noted=row.get("Notes", "")
        )
        db.session.add(sale)
    
    db.session.commit()

def main():
    app = create_app()
    with app.app_context():
        migrate_p2v_to_db()
        migrate_b2bc_to_db()
        print("Data migrated successfully.")

if __name__ == "__main__":
    main()
