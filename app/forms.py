from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FloatField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please login.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ResourceForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('Tools', 'Tools'),
        ('Electronics', 'Electronics'),
        ('Books', 'Books'),
        ('Equipment', 'Equipment'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    listing_type = SelectField('Listing Type', choices=[
        ('Rent', 'For Rent Only'),
        ('Sale', 'For Sale Only'),
        ('Both', 'For Rent & Sale')
    ], validators=[DataRequired()], default='Rent')
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    image_url = StringField('Image URL', validators=[Optional(), Length(max=255)])
    currency = SelectField('Currency', choices=[
        ('USD', 'USD ($)'),
        ('EUR', 'EUR (€)'),
        ('GBP', 'GBP (£)'),
        ('INR', 'INR (₹)'),
        ('CAD', 'CAD (C$)'),
        ('AUD', 'AUD (A$)'),
        ('JPY', 'JPY (¥)')
    ], validators=[DataRequired()], default='USD')
    daily_price = FloatField('Daily Rental Price (Optional)', validators=[Optional()])
    sale_price = FloatField('Sale Price (Optional)', validators=[Optional()])
    submit = SubmitField('List Resource')

class BookingForm(FlaskForm):
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    purpose = TextAreaField('Purpose/Reason for borrowing', validators=[DataRequired()])
    submit = SubmitField('Request Booking')

class PurchaseForm(FlaskForm):
    message = TextAreaField('Note/Message for Seller (Optional)', validators=[Optional()])
    submit = SubmitField('Confirm Purchase Request')

class MessageForm(FlaskForm):
    body = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')


