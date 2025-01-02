# views/booking.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Booking, Branch, SalesVoucherGroup
from forms import UpdateBookingForm, NewBookingForm
from utils.decorators import roles_required

booking_bp = Blueprint('booking', __name__, template_folder='bookings')

@booking_bp.route('/bookings')
@login_required
def list_bookings():
    if current_user.role == 'admin':
        bookings = Booking.query.all()
    else:
        bookings = Booking.query.filter_by(branch_id=current_user.branch_id).all()
    return render_template('bookings/list_bookings.html', bookings=bookings)

@booking_bp.route('/new', methods=['GET', 'POST'])
@login_required
@roles_required('admin','branch_staff')
def new_booking():
    """Create a brand-new booking for any sale or possibly none."""
    form = NewBookingForm()
    # Fill branches
    form.branch_id.choices = [(b.id, b.name) for b in Branch.query.all()]
    
    if form.validate_on_submit():
        booking = Booking(
            booking_name=form.booking_name.data,
            booking_date=form.booking_date.data,
            time_slot=form.time_slot.data if form.time_slot.data else None,
            status=form.status.data,
            actual_quantity=0,
            noted=form.noted.data,
            branch_id=form.branch_id.data if form.branch_id.data else None
        )
        db.session.add(booking)
        db.session.commit()
        flash("Booking created successfully!", "success")
        return redirect(url_for('booking.list_bookings'))
    
    return render_template('bookings/new_booking.html', form=form)

@booking_bp.route('/new_for_sale/<int:sale_id>', methods=['GET','POST'])
@login_required
@roles_required('admin','branch_staff')
def new_booking_for_sale(sale_id):
    """
    Create a booking specifically for an existing sale.
    This route is optional if you want to tie booking to a sale from the start.
    """
    sale = SalesVoucherGroup.query.get_or_404(sale_id)
    form = NewBookingForm()
    form.branch_id.choices = [(b.id, b.name) for b in Branch.query.all()]
    
    if form.validate_on_submit():
        booking = Booking(
            voucher_group_sale_id=sale.id,
            booking_name=form.booking_name.data,
            booking_date=form.booking_date.data,
            time_slot=form.time_slot.data if form.time_slot.data else None,
            status=form.status.data,
            actual_quantity=0,
            noted=form.noted.data,
            branch_id=form.branch_id.data if form.branch_id.data else None
        )
        db.session.add(booking)
        db.session.commit()
        flash(f"Booking created for Sale #{sale.id}!", "success")
        return redirect(url_for('booking.list_bookings'))
    
    return render_template('bookings/new_booking.html', form=form)

@booking_bp.route('/update_booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'branch_staff')
def update_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    form = UpdateBookingForm(obj=booking)
    if form.validate_on_submit():
        booking.status = form.status.data
        booking.actual_quantity = form.actual_quantity.data
        booking.noted = form.noted.data
        db.session.commit()
        flash('Booking updated successfully!', 'success')
        return redirect(url_for('booking.list_bookings'))
    return render_template('bookings/update_booking.html', form=form, booking=booking)
