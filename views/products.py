# views/products.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Product
from forms import ProductForm

products_bp = Blueprint('products', __name__, template_folder='products')

@products_bp.route('/list', methods=['GET'])
@login_required
def list_products():
    products = Product.query.order_by(Product.category, Product.name).all()
    return render_template('products/list_products.html', products=products)

@products_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.category = form.category.data
        product.default_price = form.default_price.data
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products.list_products'))
    return render_template('products/edit_product.html', form=form, product=product)

@products_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        new_prod = Product(
            name=form.name.data,
            category=form.category.data,
            default_price=form.default_price.data
        )
        db.session.add(new_prod)
        db.session.commit()
        flash('New product added!', 'success')
        return redirect(url_for('products.list_products'))
    return render_template('products/new_product.html', form=form)
