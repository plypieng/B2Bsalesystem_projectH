# views/booking.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Booking, Branch
from forms import UpdateBookingForm
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
