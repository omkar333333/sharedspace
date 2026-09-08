from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=5.0)
    trust_score = db.Column(db.Integer, default=100)
    profile_image_url = db.Column(db.String(255), nullable=True)
    cover_image_url = db.Column(db.String(255), nullable=True)
    
    resources = db.relationship('Resource', backref='owner', lazy=True)
    borrowed = db.relationship('Booking', backref='borrower', lazy=True)
    purchases = db.relationship('Purchase', backref='buyer', lazy=True)

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic'
    )
    
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def unread_message_count(self):
        return Message.query.filter_by(recipient_id=self.id, is_read=False).count()

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    availability_status = db.Column(db.String(20), nullable=False, default='Available')
    image_url = db.Column(db.String(255), nullable=True)
    daily_price = db.Column(db.Float, nullable=True)
    listing_type = db.Column(db.String(20), nullable=False, default='Rent')
    sale_price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), nullable=False, default='USD')
    qr_code_url = db.Column(db.String(255), nullable=True)
    health_status = db.Column(db.String(50), nullable=False, default='Good')
    maintenance_notes = db.Column(db.Text, nullable=True)
    security_deposit = db.Column(db.Float, nullable=True, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bookings = db.relationship('Booking', backref='resource', lazy=True)
    purchases = db.relationship('Purchase', backref='resource', lazy=True)
    maintenance_incidents = db.relationship('MaintenanceIncident', backref='resource', lazy=True)

    @property
    def currency_symbol(self):
        symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'INR': '₹',
            'CAD': 'C$',
            'AUD': 'A$',
            'JPY': '¥'
        }
        return symbols.get(self.currency, '$')

    def __repr__(self):
        return f"Resource('{self.title}', '{self.category}', '{self.availability_status}')"

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    request_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    response_date = db.Column(db.DateTime, nullable=True)
    check_in_time = db.Column(db.DateTime, nullable=True)
    check_out_time = db.Column(db.DateTime, nullable=True)
    check_out_image_url = db.Column(db.String(255), nullable=True)
    check_in_image_url = db.Column(db.String(255), nullable=True)
    
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Booking('{self.id}', '{self.status}', '{self.start_date}')"

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    request_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    response_date = db.Column(db.DateTime, nullable=True)
    price = db.Column(db.Float, nullable=False)
    
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Purchase('{self.id}', '{self.status}', '{self.price}')"

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    resource = db.relationship('Resource', backref='messages', lazy=True)

    def __repr__(self):
        return f"Message('{self.id}', '{self.sender_id}', '{self.recipient_id}')"

class MaintenanceIncident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)
    reported_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issue_description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Open')
    reported_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    
    reported_by = db.relationship('User', foreign_keys=[reported_by_id], backref='reported_incidents')

    def __repr__(self):
        return f"MaintenanceIncident('{self.id}', Resource '{self.resource_id}', Status '{self.status}')"

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications', lazy=True)

    def __repr__(self):
        return f"Notification('{self.id}', User '{self.user_id}', Read '{self.is_read}')"

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    is_damage_report = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviews_given')
    reviewee = db.relationship('User', foreign_keys=[reviewee_id], backref='reviews_received')
    booking = db.relationship('Booking', backref='review', lazy=True)

    def __repr__(self):
        return f"Review('{self.id}', Rating '{self.rating}')"

class DamageReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Open')
    reported_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    booking = db.relationship('Booking', backref='damage_reports', lazy=True)
    reporter = db.relationship('User', backref='reported_damages', lazy=True)

    def __repr__(self):
        return f"DamageReport('{self.id}', Status '{self.status}')"
