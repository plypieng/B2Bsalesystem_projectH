# views/booking.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Booking, Branch, SalesVoucherGroup
from forms import UpdateBookingForm, NewBookingForm, InlineUpdateBookingForm
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
    
    # Populate branch choices
    form.branch_id.choices = [(b.id, b.name) for b in Branch.query.all()]
    
    if form.validate_on_submit():
        # Update all relevant fields
        booking.booking_name = form.booking_name.data
        booking.booking_date = form.booking_date.data
        booking.time_slot = form.time_slot.data if form.time_slot.data else None
        booking.branch_id = form.branch_id.data if form.branch_id.data else None
        booking.status = form.status.data
        booking.actual_quantity = form.actual_quantity.data
        booking.noted = form.noted.data
        
        db.session.commit()
        flash('Booking updated successfully!', 'success')
        return redirect(url_for('booking.list_bookings'))
    
    return render_template('bookings/update_booking.html', form=form, booking=booking)

@booking_bp.route('/delete_booking/<int:booking_id>', methods=['GET'])
@login_required
@roles_required('admin', 'branch_staff')
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Check permissions
    if current_user.role != 'admin' and booking.branch_id != current_user.branch_id:
        flash('You do not have permission to delete this booking.', 'danger')
        return redirect(url_for('booking.list_bookings'))
    
    try:
        db.session.delete(booking)
        db.session.commit()
        flash(f'Booking #{booking_id} has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the booking: {str(e)}', 'danger')
    
    return redirect(url_for('booking.list_bookings'))

@booking_bp.route('/update_booking_fields/<int:booking_id>', methods=['POST'])
@login_required
@roles_required('admin', 'branch_staff')
def update_booking_fields(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Check permissions
    if current_user.role != 'admin' and booking.branch_id != current_user.branch_id:
        flash('You do not have permission to update this booking.', 'danger')
        return redirect(url_for('booking.list_bookings'))
    
    # Retrieve form data
    status = request.form.get('status')
    actual_quantity = request.form.get('actual_quantity')
    
    # Validate and update fields
    if status:
        booking.status = status
    if actual_quantity:
        try:
            booking.actual_quantity = int(actual_quantity)
        except ValueError:
            flash('Actual Quantity must be an integer.', 'danger')
            return redirect(url_for('booking.list_bookings'))
    
    try:
        db.session.commit()
        flash(f'Booking #{booking_id} has been updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while updating the booking: {str(e)}', 'danger')
    
    return redirect(url_for('booking.list_bookings'))
