# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='staff')
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    
    b2bc_sales = db.relationship('SalesB2BC', backref='salesperson', lazy=True)
    branch = db.relationship('Branch', backref='users')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username}>"

class Branch(db.Model):
    __tablename__ = 'branches'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255))
    capacity = db.Column(db.Integer, default=100)
    
    voucher_group_sales = db.relationship('SalesVoucherGroup', backref='branch', lazy=True)
    bookings = db.relationship('Booking', backref='branch', lazy=True)
    b2bc_sales = db.relationship('SalesB2BC', backref='branch', lazy=True)
    
    def __repr__(self):
        return f"<Branch {self.name}>"

class SalesVoucherGroup(db.Model):
    __tablename__ = 'sales_voucher_group'

    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    sale_type = db.Column(db.String(50), nullable=False)
    
    # We'll store only the final 'product_name' or we can remove it. 
    # We'll rely on product_id in the form, but you might store final name after selection.
    product_name = db.Column(db.String(100), nullable=True)
    
    quantity = db.Column(db.Integer, default=1)
    price_per_unit = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, default=0.0)
    vat_7 = db.Column(db.Float, default=0.0)
    total_sale = db.Column(db.Float, default=0.0)
    
    partner_name = db.Column(db.String(100))
    partner_company = db.Column(db.String(100))
    
    # Removed direct references to branch_id for now or keep it if you want
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    
    noted = db.Column(db.Text)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    salesperson_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(50), default='waiting')
    
    salesperson = db.relationship('User', backref='voucher_group_sales', foreign_keys=[salesperson_id])
    
    # The cascade line is the key to deleting without constraint errors
    bookings = db.relationship(
        'Booking',
        backref='voucher_group_sale',
        lazy=True,
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f"<SalesVoucherGroup (id={self.id}, type={self.sale_type})>"

    def compute_activity_group_price(self):
        # bracket logic
        brackets_on_site = [(10, 900), (15, 850), (20, 800), (30, 750), (40, 700), (50, 650)]
        brackets_off_site = [(20, 1300), (40, 1100), (60, 1000), (80, 950), (100, 850)]

        if 'On-site' in (self.product_name or ''):
            bracket_list = brackets_on_site
        elif 'Off-site' in (self.product_name or ''):
            bracket_list = brackets_off_site
        else:
            return

        q = self.quantity or 0
        bracket_list = sorted(bracket_list, key=lambda x: x[0])
        chosen_bracket_price = None
        for bracket_people, bracket_price in bracket_list:
            if q <= bracket_people:
                chosen_bracket_price = bracket_price
                break
        if not chosen_bracket_price:
            chosen_bracket_price = bracket_list[-1][1]

        self.price_per_unit = chosen_bracket_price

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    
    # Now allow NULL, plus ondelete='CASCADE'
    voucher_group_sale_id = db.Column(
        db.Integer, 
        db.ForeignKey('sales_voucher_group.id', ondelete='CASCADE'),
        nullable=True
    )
    booking_name = db.Column(db.String(100), nullable=True)
    
    booking_date = db.Column(db.Date)
    time_slot = db.Column(db.String(50))
    status = db.Column(db.String(50), default='booked')
    actual_quantity = db.Column(db.Integer, default=0)
    noted = db.Column(db.Text)
    
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    
    def __repr__(self):
        return f"<Booking (id={self.id}, name={self.booking_name}, status={self.status})>"

class SalesB2BC(db.Model):
    __tablename__ = 'sales_b2bc'

    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    course_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, default=0.0)
    commission_rate = db.Column(db.Float, default=0.0)
    commission_amount = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))
    noted = db.Column(db.Text)

    def __repr__(self):
        return f"<SalesB2BC (id={self.id}, course={self.course_name})>"

class CommissionRule(db.Model):
    __tablename__ = 'commission_rules'

    id = db.Column(db.Integer, primary_key=True)
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<CommissionRule {self.min_amount} - {self.max_amount} @ {self.rate}>"

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    default_price = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)

    def __repr__(self):
        return f"<Product {self.name} (category={self.category}, price={self.default_price})>"
