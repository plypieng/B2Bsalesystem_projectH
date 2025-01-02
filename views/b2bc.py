# views/b2bc.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, SalesB2BC, Branch, CommissionRule
from forms import B2BCSaleForm
from utils.decorators import roles_required

b2bc_bp = Blueprint('b2bc', __name__, template_folder='b2bc')

@b2bc_bp.route('/new_b2bc_sale', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'branch_staff')
def new_b2bc_sale():
    form = B2BCSaleForm()
    form.branch.choices = [(branch.id, branch.name) for branch in Branch.query.all()]
    if form.validate_on_submit():
        course_name = form.course_name.data
        price = float(form.price.data)
        
        # Determine commission rate based on rules
        commission_rule = CommissionRule.query.filter(
            price >= CommissionRule.min_amount,
            price <= CommissionRule.max_amount
        ).first()
        if not commission_rule:
            commission_rate = 0.0
        else:
            commission_rate = commission_rule.rate
        commission_amount = price * commission_rate
        
        branch_id = form.branch.data
        noted = form.noted.data
        
        sale = SalesB2BC(
            course_name=course_name,
            price=price,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            user_id=current_user.id,
            branch_id=branch_id,
            noted=noted
        )
        db.session.add(sale)
        db.session.commit()
        
        flash('B2BC sale recorded successfully!', 'success')
        return redirect(url_for('b2bc.list_b2bc_sales'))
    
    return render_template('b2bc/new_b2bc_sale.html', form=form)

@b2bc_bp.route('/b2bc_sales')
@login_required
def list_b2bc_sales():
    if current_user.role == 'admin':
        sales = SalesB2BC.query.all()
    else:
        sales = SalesB2BC.query.filter_by(branch_id=current_user.branch_id).all()
    return render_template('b2bc/list_b2bc_sales.html', sales=sales)
