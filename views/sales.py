# views/sales.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, SalesVoucherGroup, User, Product
from forms import VoucherGroupSaleForm
from utils.decorators import roles_required

sales_bp = Blueprint('sales', __name__, template_folder='sales')

@sales_bp.route('/voucher_group_sales', methods=['GET', 'POST'])
@login_required
def list_voucher_group_sales():
    # If POST is from inline status change
    if request.method == 'POST':
        sale_id = request.form.get('sale_id')
        new_status = request.form.get('status')
        if sale_id and new_status:
            sale = SalesVoucherGroup.query.get(sale_id)
            if sale and (current_user.role == 'admin' or sale.salesperson_id == current_user.id):
                sale.status = new_status
                db.session.commit()
                flash(f"Sale #{sale_id} status changed to {new_status}.", "success")
        return redirect(url_for('sales.list_voucher_group_sales'))
    
    # GET logic (month filter)
    month_filter = request.args.get('month')
    query = SalesVoucherGroup.query
    if current_user.role != 'admin':
        # filter by branch or user if you want
        pass
    
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
    # Populate the product dropdown
    products = Product.query.order_by(Product.name).all()
    form.product_id.choices = [(p.id, p.name) for p in products]
    
    if form.validate_on_submit():
        product = Product.query.get(form.product_id.data)
        if not product:
            flash("Invalid product selected.", "danger")
            return redirect(url_for('sales.new_voucher_group_sale'))
        
        # auto-assign sale_type from product category
        sale_type = 'group' if product.category == 'activities_group' else 'voucher'
        
        quantity = float(form.quantity.data)
        price_per_unit = float(form.price_per_unit.data)
        
        total_price = quantity * price_per_unit
        vat_7 = total_price * 0.07
        total_sale = total_price + vat_7
        
        sale = SalesVoucherGroup(
            sale_type=sale_type,
            product_name=product.name,
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
        
        # IMPORTANT: We do NOT create a booking automatically.
        
        flash('Voucher/Group sale created successfully! (Currently "Not booked")', 'success')
        return redirect(url_for('sales.list_voucher_group_sales'))
    
    return render_template('sales/new_voucher_group_sale.html', form=form)

@sales_bp.route('/edit_sale/<int:sale_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'branch_staff')
def edit_sale(sale_id):
    sale = SalesVoucherGroup.query.get_or_404(sale_id)
    form = VoucherGroupSaleForm(obj=sale)
    products = Product.query.order_by(Product.name).all()
    form.product_id.choices = [(p.id, p.name) for p in products]
    
    # find matching product
    matching_product = Product.query.filter_by(name=sale.product_name).first()
    
    if request.method == 'GET':
        if matching_product:
            form.product_id.data = matching_product.id
        form.status.data = sale.status
        # no booking auto creation
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
        
        if sale.bookings:
            # update booking name if it exists
            sale.bookings[0].booking_name = form.booking_name.data
            db.session.commit()
        
        flash(f"Sale #{sale.id} updated successfully!", "success")
        return redirect(url_for('sales.list_voucher_group_sales'))
    
    return render_template('sales/new_voucher_group_sale.html', form=form, editing=True)

@sales_bp.route('/delete_sale/<int:sale_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'branch_staff')
def delete_sale(sale_id):
    sale = SalesVoucherGroup.query.get_or_404(sale_id)
    db.session.delete(sale)
    db.session.commit()
    flash(f"Sale #{sale_id} has been deleted.", "success")
    return redirect(url_for('sales.list_voucher_group_sales'))

@sales_bp.route('/view_sale/<int:sale_id>')
@login_required
@roles_required('admin', 'branch_staff')
def view_sale(sale_id):
    sale = SalesVoucherGroup.query.get_or_404(sale_id)
    return render_template('sales/view_sale.html', sale=sale)
