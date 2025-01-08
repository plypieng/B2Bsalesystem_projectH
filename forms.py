# forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, BooleanField, SelectField,
    FloatField, TextAreaField, HiddenField, IntegerField, DateField
)
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, ValidationError
import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('branch_staff', 'Branch Staff'), ('staff', 'Staff')], validators=[DataRequired()])
    branch = SelectField('Branch', coerce=int, validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate(self):
        if not super(RegistrationForm, self).validate():
            return False
        if self.role.data == 'branch_staff' and not self.branch.data:
            self.branch.errors.append('Branch is required for branch staff.')
            return False
        return True

class VoucherGroupSaleForm(FlaskForm):
    id = HiddenField("ID")  # For editing existing record
    sale_type = SelectField('Sale Type', choices=[('voucher', 'Voucher'), ('group', 'Group')], validators=[DataRequired()])
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    
    partner_name = StringField('Partner Name', validators=[Optional(), Length(max=100)])
    partner_company = StringField('Partner Company', validators=[Optional(), Length(max=100)])
    
    booking_name = StringField('Booking Name', validators=[Optional(), Length(max=100)])
    
    quantity = FloatField('Quantity', validators=[DataRequired()])
    price_per_unit = FloatField('Price per Unit (THB)', validators=[DataRequired()])
    
    status = SelectField(
        'Status',
        choices=[('waiting', 'Waiting for Payment'), ('paid', 'Paid'), ('canceled', 'Canceled')],
        validators=[DataRequired()],
        default='waiting'
    )
    
    noted = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Submit Sale')

class B2BCSaleForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired(), Length(max=100)])
    price = FloatField('Price', validators=[DataRequired()])
    noted = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Record Sale')

class UpdateBookingForm(FlaskForm):
    booking_name = StringField('Booking Name', validators=[Optional(), Length(max=100)])
    booking_date = DateField('Booking Date', validators=[Optional()])  # can be optional
    time_slot = SelectField('Time Slot', choices=[
        ('08:00','08:00'), ('09:00','09:00'), ('10:00','10:00'),
        ('11:00','11:00'), ('13:00','13:00'), ('14:00','14:00'),
        ('15:00','15:00'), ('16:00','16:00'), ('17:00','17:00')
    ], validators=[Optional()])
    
    branch_id = SelectField('Branch', coerce=int, validators=[Optional()])
    
    status = SelectField('Status', choices=[
        ('not_booked', 'Not Booked'),
        ('booked','Booked'),
        ('confirmed','Confirmed'),
        ('used','Used'),
        ('canceled','Canceled')
    ], validators=[DataRequired()])
    
    actual_quantity = IntegerField('Actual Quantity', validators=[DataRequired()])
    noted = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Update Booking')
    
    def validate_booking_date(form, field):
        if field.data and field.data < datetime.date.today():
            raise ValidationError("Booking date cannot be in the past.")
        
class NewBookingForm(FlaskForm):
    booking_name = StringField('Booking Name', validators=[Optional(), Length(max=100)])
    booking_date = DateField('Booking Date', validators=[Optional()])  # can be optional
    time_slot = SelectField('Time Slot', choices=[
        ('08:00','08:00'), ('09:00','09:00'), ('10:00','10:00'),
        ('11:00','11:00'), ('13:00','13:00'), ('14:00','14:00'),
        ('15:00','15:00'), ('16:00','16:00'), ('17:00','17:00')
    ], validators=[Optional()])
    
    branch_id = SelectField('Branch', coerce=int, validators=[Optional()])
    
    status = SelectField('Status', choices=[
        ('not_booked', 'Not Booked'),
        ('booked','Booked'),
        ('confirmed','Confirmed'),
        ('used','Used'),
        ('canceled','Canceled')
    ], default='not_booked')
    
    noted = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Create Booking')
    
    def validate_booking_date(form, field):
        if field.data and field.data < datetime.date.today():
            raise ValidationError("Booking date cannot be in the past.")

# New Inline Update Form
class InlineUpdateBookingForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('not_booked', 'Not Booked'),
        ('booked','Booked'),
        ('confirmed','Confirmed'),
        ('used','Used'),
        ('canceled','Canceled')
    ], validators=[DataRequired()])
    actual_quantity = IntegerField('Actual Quantity', validators=[DataRequired()])
    submit = SubmitField('Update')

class ProductForm(FlaskForm):
    id = HiddenField("ID")
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    category = StringField("Category", validators=[DataRequired(), Length(max=50)])
    default_price = FloatField("Price", validators=[DataRequired()])
    submit = SubmitField("Save")