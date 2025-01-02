# views/sales.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, SalesVoucherGroup, Branch, Booking, User, Product
from forms import VoucherGroupSaleForm
from utils.decorators import roles_required

sales_bp = Blueprint('sales', __name__, template_folder='sales')

@sales_bp.route('/voucher_group_sales', methods=['GET', 'POST'])
@login_required
def list_voucher_group_sales():
    """List all voucher/group sales with optional month filter & inline status update."""
    # 1) If POST is coming from inline status change
    if request.method == 'POST':
        sale_id = request.form.get('sale_id')
        new_status = request.form.get('status')
        if sale_id and new_status:
            sale = SalesVoucherGroup.query.get(sale_id)
            if sale and (current_user.role == 'admin' or sale.branch_id == current_user.branch_id):
                sale.status = new_status
                db.session.commit()
                flash(f"Sale #{sale_id} status changed to {new_status}.", "success")
        return redirect(url_for('sales.list_voucher_group_sales'))
    
    # 2) GET logic
    month_filter = request.args.get('month')  # e.g. "2025-01"
    query = SalesVoucherGroup.query

    if current_user.role != 'admin':
        query = query.filter_by(branch_id=current_user.branch_id)

    if month_filter:
        try:
            year, month = month_filter.split('-')
            year = int(year)
            month = int(month)
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year+1, 1, 1)
            else:
                end_date = datetime(year, month+1, 1)
            query = query.filter(SalesVoucherGroup.sale_date >= start_date,
                                 SalesVoucherGroup.sale_date < end_date)
        except:
            pass
    
    sales = query.all()
    
    return render_template('sales/list_voucher_group_sales.html',
                           sales=sales,
                           month_filter=month_filter)

@sales_bp.route('/new_voucher_group_sale', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'branch_staff')
def new_voucher_group_sale():
    form = VoucherGroupSaleForm()
    
    # Populate the product dropdown with your "registered" products
    products = Product.query.order_by(Product.name).all()
    form.product_id.choices = [(p.id, p.name) for p in products]
    
    if form.validate_on_submit():
        # Identify the chosen product
        product = Product.query.get(form.product_id.data)
        if not product:
            flash("Invalid product selected.", "danger")
            return redirect(url_for('sales.new_voucher_group_sale'))
        
        # auto-assign sale_type from product category (or you can do your own logic)
        sale_type = 'group' if product.category == 'activities_group' else 'voucher'
        
        quantity = float(form.quantity.data)
        price_per_unit = float(form.price_per_unit.data)
        
        total_price = quantity * price_per_unit
        vat_7 = total_price * 0.07
        total_sale = total_price + vat_7
        
        sale = SalesVoucherGroup(
            sale_type=sale_type,
            product_name=product.name,  # store final name
            quantity=quantity,
            price_per_unit=price_per_unit,
            total_price=total_price,
            vat_7=vat_7,
            total_sale=total_sale,
            partner_name=form.partner_name.data,
            partner_company=form.partner_company.data,
            status=form.status.data,
            noted=form.noted.data,
            salesperson_id=current_user.id
        )
        
        db.session.add(sale)
        db.session.commit()
        
        # Create a minimal booking record automatically
        # booking_name from form, status='pending' or 'booked'
        booking = Booking(
            voucher_group_sale_id=sale.id,
            booking_name=form.booking_name.data or f"Booking for Sale {sale.id}",
            status='booked'
        )
        db.session.add(booking)
        db.session.commit()
        
        flash('Voucher/Group sale created successfully!', 'success')
        return redirect(url_for('sales.list_voucher_group_sales'))
    
    return render_template('sales/new_voucher_group_sale.html', form=form)

@sales_bp.route('/edit_sale/<int:sale_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'branch_staff')
def edit_sale(sale_id):
    """A more user-friendly edit mode with auto-populating product info and better UI."""
    sale = SalesVoucherGroup.query.get_or_404(sale_id)
    if current_user.role != 'admin':
        # optionally check sale's salesperson_id == current_user.id, or the branch
        pass
    
    form = VoucherGroupSaleForm(obj=sale)
    
    # Load products
    products = Product.query.order_by(Product.name).all()
    form.product_id.choices = [(p.id, p.name) for p in products]
    
    # Find the product that matches sale.product_name, if any
    # (In real code, you'd have stored product_id. For now, let's guess.)
    matching_product = Product.query.filter_by(name=sale.product_name).first()
    default_pid = matching_product.id if matching_product else None
    
    if request.method == 'GET':
        if matching_product:
            form.product_id.data = matching_product.id
        form.status.data = sale.status
        form.booking_name.data = ''  # We'll set it from sale's booking if we want
        # if there's a booking for this sale, we can prefill booking_name
        if sale.bookings:
            form.booking_name.data = sale.bookings[0].booking_name or ''
    
    if form.validate_on_submit():
        product = Product.query.get(form.product_id.data)
        if not product:
            flash("Invalid product selection!", "danger")
            return redirect(url_for('sales.edit_sale', sale_id=sale.id))
        
        sale_type = 'group' if product.category == 'activities_group' else 'voucher'
        sale.sale_type = sale_type
        sale.product_name = product.name
        
        sale.partner_name = form.partner_name.data
        sale.partner_company = form.partner_company.data
        
        sale.quantity = float(form.quantity.data)
        sale.price_per_unit = float(form.price_per_unit.data)
        sale.status = form.status.data
        sale.noted = form.noted.data
        
        sale.total_price = sale.quantity * sale.price_per_unit
        sale.vat_7 = sale.total_price * 0.07
        sale.total_sale = sale.total_price + sale.vat_7
        
        db.session.commit()
        
        # Also update booking name if a booking exists
        if sale.bookings:
            sale.bookings[0].booking_name = form.booking_name.data
            db.session.commit()
        
        flash(f"Sale #{sale.id} updated successfully!", "success")
        return redirect(url_for('sales.list_voucher_group_sales'))
    
    return render_template('sales/new_voucher_group_sale.html', form=form, editing=True)

@sales_bp.route('/delete_sale/<int:sale_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'branch_staff')
def delete_sale(sale_id):
    """Deletes the sale + associated bookings (cascade)."""
    sale = SalesVoucherGroup.query.get_or_404(sale_id)
    # if not admin, optionally check the branch or user
    db.session.delete(sale)  # cascade will remove associated bookings
    db.session.commit()
    flash(f"Sale #{sale_id} has been deleted.", "success")
    return redirect(url_for('sales.list_voucher_group_sales'))

@sales_bp.route('/view_sale/<int:sale_id>')
@login_required
@roles_required('admin', 'branch_staff')
def view_sale(sale_id):
    sale = SalesVoucherGroup.query.get_or_404(sale_id)
    return render_template('sales/view_sale.html', sale=sale)
