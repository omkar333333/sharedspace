from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FloatField, DateField
from flask_wtf.file import FileField, FileAllowed
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

class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_picture = FileField('Update Profile Picture', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'])])
    cover_picture = FileField('Update Cover Photo', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already registered.')

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
    latitude = FloatField('Latitude (Optional, e.g. 42.3601)', validators=[Optional()])
    longitude = FloatField('Longitude (Optional, e.g. -71.0942)', validators=[Optional()])
    image_url = StringField('Image URL', validators=[Optional(), Length(max=255)])
    image_file = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
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
    security_deposit = FloatField('Security Deposit (Optional)', validators=[Optional()])
    submit = SubmitField('List Resource')

class BookingForm(FlaskForm):
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    purpose = TextAreaField('Purpose/Reason for borrowing', validators=[DataRequired()])
    agree_to_terms = BooleanField('I agree to pay the full replacement cost if I damage or lose this item.', validators=[DataRequired()])
    submit = SubmitField('Request Booking')

class PurchaseForm(FlaskForm):
    message = TextAreaField('Message to Owner (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Request to Purchase')

class ConditionReportForm(FlaskForm):
    health_status = SelectField('Equipment Condition', choices=[
        ('Good', 'Good - No issues'),
        ('Minor Issue', 'Minor Issue - Usable but needs attention'),
        ('Damaged', 'Damaged - Unusable or broken')
    ], validators=[DataRequired()])
    maintenance_notes = TextAreaField('Describe the issue (if any)', validators=[Optional(), Length(max=500)])
    image_file = FileField('Upload Condition Photo (Optional but recommended)', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Complete Return')

class CheckInForm(FlaskForm):
    image_file = FileField('Upload "Before" Photo (Condition at Check-in)', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Complete Check-in')

class MessageForm(FlaskForm):
    body = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class DamageReportForm(FlaskForm):
    description = TextAreaField('Describe the damage in detail', validators=[DataRequired(), Length(min=10, max=1000)])
    image_file = FileField('Upload Evidence (Photo)', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Submit Damage Report')

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[
        ('5', '5 Stars - Excellent'),
        ('4', '4 Stars - Good'),
        ('3', '3 Stars - Okay'),
        ('2', '2 Stars - Poor'),
        ('1', '1 Star - Terrible')
    ], validators=[DataRequired()])
    comment = TextAreaField('Review Comments (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit Review')
