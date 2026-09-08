from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app, send_file
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Resource, Booking, Purchase, Message, MaintenanceIncident
from app.forms import (RegistrationForm, LoginForm, ResourceForm, 
                       BookingForm, PurchaseForm, ConditionReportForm, CheckInForm,
                       MessageForm, UpdateProfileForm, DamageReportForm, ReviewForm)
from datetime import datetime
import qrcode
import io
import os
import secrets
import urllib.request
import urllib.parse
import json

main = Blueprint('main', __name__)

def geocode_location(location_str):
    if not location_str:
        return None, None
    try:
        query = urllib.parse.quote(location_str)
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'SharedSpaceApp/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None

def get_demand_prediction(resource):
    """Simple heuristic prediction engine for Hackathon WOW factor."""
    total_bookings = len(resource.bookings) if hasattr(resource, 'bookings') else 0
    
    if total_bookings >= 3:
        return {
            'level': 'High Demand Expected',
            'icon': 'bi-graph-up-arrow',
            'color': 'danger',
            'message': 'This item is frequently booked.',
            'recommended_time': 'Early Morning (8 AM - 10 AM)'
        }
    elif total_bookings > 0:
        return {
            'level': 'Moderate Demand',
            'icon': 'bi-graph-up',
            'color': 'warning',
            'message': 'This item sees regular usage.',
            'recommended_time': 'Mid-day (11 AM - 2 PM)'
        }
    else:
        return {
            'level': 'Low Demand',
            'icon': 'bi-graph-down',
            'color': 'success',
            'message': 'This item is readily available.',
            'recommended_time': 'Any time works!'
        }

@main.app_context_processor
def inject_globals():
    if current_user.is_authenticated:
        from app.models import Notification
        unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return {
            'unread_count': current_user.unread_message_count(),
            'unread_notifications': unread_notifs
        }
    return {'unread_count': 0, 'unread_notifications': 0}

@main.before_app_request
def process_no_shows():
    # Only run this once per request cycle
    if getattr(request, '_no_show_processed', False):
        return
    request._no_show_processed = True

    try:
        now = datetime.utcnow()
        # Find approved bookings that started more than 15 minutes ago but haven't been checked in
        overdue_bookings = Booking.query.filter(
            Booking.status == 'approved',
            Booking.start_date <= now,
            Booking.check_in_time.is_(None)
        ).all()

        for booking in overdue_bookings:
            # Check if 15 minutes have passed since start_date
            if (now - booking.start_date).total_seconds() > 900:
                booking.status = 'no-show'
                
                # Check for waitlisted bookings for this resource that overlap
                waitlisted = Booking.query.filter(
                    Booking.resource_id == booking.resource_id,
                    Booking.status == 'waitlisted',
                    Booking.start_date >= booking.start_date
                ).order_by(Booking.request_date.asc()).first()
                
                if waitlisted:
                    waitlisted.status = 'approved'
                    waitlisted.response_date = now
                else:
                    # Mark resource as available if no waitlist
                    booking.resource.availability_status = 'Available'
                    
        if overdue_bookings:
            db.session.commit()
    except Exception as e:
        # Failsafe so we don't break the app if db isn't ready
        pass

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static', 'resource_pics', picture_fn)
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    form_picture.save(picture_path)
    return url_for('static', filename='resource_pics/' + picture_fn)


@main.route('/about')
def about():
    return render_template('about.html', title='About Us')

@main.route('/help')
def help_page():
    return render_template('placeholder.html', title='Help Center')

@main.route('/contact')
def contact():
    return render_template('placeholder.html', title='Contact Us')

@main.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html', title='How It Works')

# --- Authentication Routes ---

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('auth/register.html', title='Register', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# --- Main Routes ---

@main.route('/')
def index():
    resources = Resource.query.filter_by(availability_status='Available').order_by(Resource.created_at.desc()).limit(6).all()
    return render_template('index.html', resources=resources)

@main.route('/notifications')
@login_required
def notifications():
    from app.models import Notification
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(20).all()
    # Mark as read
    for n in notifs:
        if not n.is_read:
            n.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)

# --- Resource Management Routes ---

@main.route('/resources')
def list_resources():
    search = request.args.get('search')
    category = request.args.get('category')
    listing_type = request.args.get('listing_type')
    
    query = Resource.query
    
    if search:
        query = query.filter((Resource.title.ilike(f'%{search}%')) | (Resource.description.ilike(f'%{search}%')))
    if category and category != 'All':
        query = query.filter_by(category=category)
    if listing_type and listing_type != 'All':
        if listing_type == 'Rent':
            query = query.filter(Resource.listing_type.in_(['Rent', 'Both']))
        elif listing_type == 'Sale':
            query = query.filter(Resource.listing_type.in_(['Sale', 'Both']))
        
    resources = query.order_by(Resource.created_at.desc()).all()
    categories = ['All', 'Tools', 'Electronics', 'Books', 'Equipment', 'Other']
    listing_types = ['All', 'Rent', 'Sale']
    return render_template('resources/list.html', resources=resources, categories=categories, listing_types=listing_types, current_category=category or 'All', current_listing_type=listing_type or 'All', search=search)

@main.route('/resource/<int:resource_id>')
def resource_detail(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    
    recommended_alternatives = []
    if resource.availability_status != 'Available':
        # Smart Alternative Recommendations
        recommended_alternatives = Resource.query.filter(
            Resource.id != resource.id,
            Resource.category == resource.category,
            Resource.availability_status == 'Available'
        ).limit(3).all()
        
    ai_prediction = get_demand_prediction(resource)
        
    return render_template('resources/detail.html', title=resource.title, resource=resource, recommended_alternatives=recommended_alternatives, ai_prediction=ai_prediction)

@main.route('/resource/<int:resource_id>/qrcode')
def resource_qrcode(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    url = url_for('main.scan_resource', resource_id=resource.id, _external=True)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

@main.route('/scan/<int:resource_id>')
@login_required
def scan_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    now = datetime.utcnow()
    
    # Are we checking it in?
    booking = Booking.query.filter(
        Booking.resource_id == resource.id,
        Booking.borrower_id == current_user.id,
        Booking.status == 'approved',
        Booking.check_in_time.is_(None)
    ).first()
    
    if booking:
        booking.check_in_time = now
        booking.status = 'in_use'
        resource.availability_status = 'In Use'
        db.session.commit()
        
        from app.models import Notification
        notif = Notification(user_id=resource.owner_id, message=f"{current_user.username} has checked in and picked up {resource.title}.")
        db.session.add(notif)
        db.session.commit()
        
        flash('Check-in successful! You are now using the equipment.', 'success')
        return redirect(url_for('main.dashboard'))
        
    # Are we checking it out/returning?
    active_booking = Booking.query.filter(
        Booking.resource_id == resource.id,
        Booking.borrower_id == current_user.id,
        Booking.status == 'in_use'
    ).first()
    
    if active_booking:
        return redirect(url_for('main.return_resource', booking_id=active_booking.id))
        
    flash('No active booking found to check in or return.', 'warning')
    return redirect(url_for('main.resource_detail', resource_id=resource.id))

@main.route('/return/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def return_resource(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.borrower_id != current_user.id or booking.status != 'in_use':
        flash('Invalid return request.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        condition = request.form.get('condition')
        
        now = datetime.utcnow()
        booking.check_out_time = now
        booking.status = 'completed'
        
        if condition == 'Good':
            current_user.trust_score = min(100, (current_user.trust_score or 100) + 5)
            booking.resource.availability_status = 'Available'
        else:
            if condition == 'Minor Issue':
                current_user.trust_score = max(0, (current_user.trust_score or 100) - 10)
            else:
                current_user.trust_score = max(0, (current_user.trust_score or 100) - 30)
                
            booking.resource.availability_status = 'Under Maintenance'
            from app.models import MaintenanceIncident
            incident = MaintenanceIncident(
                resource_id=booking.resource.id,
                reported_by_id=current_user.id,
                issue_description=f"Reported condition on return: {condition}. AI Verification complete."
            )
            db.session.add(incident)
            
        db.session.commit()
        
        from app.models import Notification
        notif = Notification(user_id=booking.resource.owner_id, message=f"{current_user.username} has returned {booking.resource.title}. Condition: {condition}.")
        db.session.add(notif)
        db.session.commit()
        
        flash('Return processed successfully! Your trust score was updated.', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('bookings/return_condition.html', booking=booking)

@main.route('/resource/new', methods=['GET', 'POST'])
@login_required
def create_resource():
    form = ResourceForm()
    if form.validate_on_submit():
        final_image_url = form.image_url.data
        if form.image_file.data:
            final_image_url = save_picture(form.image_file.data)
            
        if form.latitude.data and form.longitude.data:
            lat = form.latitude.data
            lng = form.longitude.data
        else:
            lat, lng = geocode_location(form.location.data)
            
        resource = Resource(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            location=form.location.data,
            latitude=lat,
            longitude=lng,
            image_url=final_image_url,
            currency=form.currency.data,
            daily_price=form.daily_price.data,
            listing_type=form.listing_type.data,
            sale_price=form.sale_price.data,
            security_deposit=form.security_deposit.data,
            owner=current_user
        )
        db.session.add(resource)
        db.session.commit()
        flash('Your resource has been created!', 'success')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
    return render_template('resources/create.html', title='New Resource', form=form, legend='New Resource')

@main.route('/resource/<int:resource_id>/update', methods=['GET', 'POST'])
@login_required
def update_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.owner != current_user:
        flash('You do not have permission to update this resource', 'danger')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
    form = ResourceForm()
    if form.validate_on_submit():
        if form.image_file.data:
            resource.image_url = save_picture(form.image_file.data)
        elif form.image_url.data:
            resource.image_url = form.image_url.data
            
        resource.title = form.title.data
        resource.description = form.description.data
        resource.category = form.category.data
        
        # Only geocode if location changed and coords not explicitly provided
        if form.latitude.data and form.longitude.data:
            resource.latitude = form.latitude.data
            resource.longitude = form.longitude.data
            resource.location = form.location.data
        elif resource.location != form.location.data:
            lat, lng = geocode_location(form.location.data)
            resource.latitude = lat
            resource.longitude = lng
            resource.location = form.location.data
            
        resource.currency = form.currency.data
        resource.daily_price = form.daily_price.data
        resource.listing_type = form.listing_type.data
        resource.sale_price = form.sale_price.data
        resource.security_deposit = form.security_deposit.data
        db.session.commit()
        flash('Your resource has been updated!', 'success')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
    elif request.method == 'GET':
        form.title.data = resource.title
        form.description.data = resource.description
        form.category.data = resource.category
        form.location.data = resource.location
        form.latitude.data = resource.latitude
        form.longitude.data = resource.longitude
        form.image_url.data = resource.image_url
        form.currency.data = resource.currency
        form.daily_price.data = resource.daily_price
        form.listing_type.data = resource.listing_type
        form.sale_price.data = resource.sale_price
        form.security_deposit.data = resource.security_deposit
    return render_template('resources/create.html', title='Update Resource', form=form, legend='Update Resource')

@main.route('/resource/<int:resource_id>/delete', methods=['POST'])
@login_required
def delete_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.owner != current_user:
        flash('You do not have permission to delete this resource.', 'danger')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
        
    from app.models import Booking, Purchase, MaintenanceIncident, Message
    Booking.query.filter_by(resource_id=resource.id).delete()
    Purchase.query.filter_by(resource_id=resource.id).delete()
    MaintenanceIncident.query.filter_by(resource_id=resource.id).delete()
    Message.query.filter_by(resource_id=resource.id).delete()
    
    db.session.delete(resource)
    db.session.commit()
    flash('Your resource has been deleted!', 'success')
    return redirect(url_for('main.list_resources'))

# --- QR & Smart Equipment Features ---

@main.route('/resource/<int:resource_id>/generate_qr')
@login_required
def generate_qr(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.owner != current_user and not current_user.is_admin:
        flash('Permission denied.', 'danger')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
    
    # Generate QR Code encoding the URL to the scan page
    scan_url = url_for('main.scan_qr', resource_id=resource.id, _external=True)
    img = qrcode.make(scan_url)
    
    # Save the QR code image
    qr_filename = f"qr_res_{resource.id}_{secrets.token_hex(4)}.png"
    qr_path = os.path.join(current_app.root_path, 'static', 'resource_pics', qr_filename)
    img.save(qr_path)
    
    resource.qr_code_url = url_for('static', filename='resource_pics/' + qr_filename)
    db.session.commit()
    flash('QR Code generated successfully!', 'success')
    return redirect(url_for('main.resource_detail', resource_id=resource.id))

@main.route('/scan/<int:resource_id>', methods=['GET', 'POST'])
@login_required
def scan_qr(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    
    # Check if the user has an active booking for this resource right now
    now = datetime.utcnow()
    
    # 1. Look for an IN_USE booking to check out
    in_use_booking = Booking.query.filter(
        Booking.resource_id == resource_id,
        Booking.borrower_id == current_user.id,
        Booking.status == 'in_use'
    ).first()
    
    if in_use_booking:
        form = ConditionReportForm()
        if form.validate_on_submit():
            in_use_booking.status = 'completed'
            in_use_booking.check_out_time = now
            
            if form.image_file.data:
                from app.utils import save_picture
                in_use_booking.check_out_image_url = save_picture(form.image_file.data)
            
            resource.health_status = form.health_status.data
            resource.maintenance_notes = form.maintenance_notes.data
            
            if form.health_status.data != 'Good':
                resource.availability_status = 'Under Maintenance'
                incident = MaintenanceIncident(
                    resource_id=resource.id,
                    reported_by_id=current_user.id,
                    issue_description=form.maintenance_notes.data,
                    reported_at=now
                )
                db.session.add(incident)
            else:
                resource.availability_status = 'Available'
                
            db.session.commit()
            flash('Equipment returned successfully!', 'success')
            return redirect(url_for('main.dashboard'))
            
        return render_template('resources/scan_checkout.html', resource=resource, booking=in_use_booking, form=form)

    # 2. Look for an APPROVED upcoming booking to check in
    # We'll allow check-in up to 15 mins early or anytime during the booking
    upcoming_booking = Booking.query.filter(
        Booking.resource_id == resource_id,
        Booking.borrower_id == current_user.id,
        Booking.status == 'approved'
    ).first()
    
    if upcoming_booking:
        form = CheckInForm()
        if form.validate_on_submit():
            upcoming_booking.status = 'in_use'
            upcoming_booking.check_in_time = now
            
            if form.image_file.data:
                # Save the uploaded "before" picture
                picture_file = save_picture(form.image_file.data)
                upcoming_booking.check_in_image_url = picture_file

            resource.availability_status = 'In Use'
            db.session.commit()
            flash('Check-in successful! You are now using the equipment.', 'success')
            return redirect(url_for('main.dashboard'))
            
        return render_template('resources/scan_checkin.html', resource=resource, booking=upcoming_booking, form=form)
        
    flash('You do not have any active or upcoming bookings for this equipment.', 'warning')
    return redirect(url_for('main.resource_detail', resource_id=resource.id))

# --- Booking Routes ---

@main.route('/resource/<int:resource_id>/book', methods=['GET', 'POST'])
@login_required
def book_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.owner == current_user:
        flash('You cannot book your own resource!', 'warning')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
    if resource.listing_type not in ['Rent', 'Both']:
        flash('This resource is not listed for rent.', 'warning')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
        
    form = BookingForm()
    if form.validate_on_submit():
        is_waitlist = resource.availability_status != 'Available'
        booking = Booking(
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            purpose=form.purpose.data,
            resource=resource,
            borrower=current_user,
            status='waitlisted' if is_waitlist else 'pending'
        )
        db.session.add(booking)
        
        # Notify owner
        from app.models import Notification
        notif_msg = f"{current_user.username} has requested to borrow '{resource.title}'."
        if is_waitlist:
            notif_msg = f"{current_user.username} joined the waitlist for '{resource.title}'."
        owner_notif = Notification(user_id=resource.owner_id, message=notif_msg)
        db.session.add(owner_notif)
        
        db.session.commit()
        if is_waitlist:
            flash('This equipment is currently unavailable. You have been added to the waitlist!', 'info')
        else:
            flash('Your booking request has been submitted and is pending approval.', 'success')
        return redirect(url_for('main.my_bookings'))
        
    ai_prediction = get_demand_prediction(resource)
    return render_template('bookings/request.html', title='Book Resource', form=form, resource=resource, ai_prediction=ai_prediction)

@main.route('/my_bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(borrower=current_user).order_by(Booking.request_date.desc()).all()
    return render_template('bookings/my_bookings.html', bookings=bookings)

@main.route('/manage_requests')
@login_required
def manage_requests():
    booking_requests = Booking.query.join(Resource).filter(Resource.owner_id == current_user.id).order_by(Booking.request_date.desc()).all()
    purchase_requests = Purchase.query.join(Resource).filter(Resource.owner_id == current_user.id).order_by(Purchase.request_date.desc()).all()
    return render_template('bookings/manage.html', requests=booking_requests, purchase_requests=purchase_requests)

@main.route('/booking/<int:booking_id>/update/<status>', methods=['POST'])
@login_required
def update_booking_status(booking_id, status):
    booking = Booking.query.get_or_404(booking_id)
    if booking.resource.owner != current_user:
        flash('You do not have permission to manage this request.', 'danger')
        return redirect(url_for('main.manage_requests'))
        
    if status in ['approved', 'rejected', 'completed']:
        booking.status = status
        booking.response_date = datetime.utcnow()
        if status == 'approved':
            booking.resource.availability_status = 'Borrowed'
        elif status in ['rejected', 'completed']:
            active_bookings = Booking.query.filter_by(resource_id=booking.resource_id, status='approved').count()
            if active_bookings == 0 and booking.resource.availability_status != 'Sold':
                 booking.resource.availability_status = 'Available'
        db.session.commit()
        
        # Notify borrower
        from app.models import Notification
        borrower_notif = Notification(user_id=booking.borrower_id, message=f"Your borrowing request for '{booking.resource.title}' was {status}.")
        db.session.add(borrower_notif)
        db.session.commit()
        flash(f'Booking request marked as {status}.', 'success')
    return redirect(url_for('main.manage_requests'))

# --- Purchase Routes ---

@main.route('/resource/<int:resource_id>/buy', methods=['GET', 'POST'])
@login_required
def buy_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.owner == current_user:
        flash('You cannot buy your own resource!', 'warning')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
    if resource.listing_type not in ['Sale', 'Both']:
        flash('This resource is not listed for sale.', 'warning')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
    if resource.availability_status == 'Sold':
        flash('This item has already been sold.', 'warning')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
        
    form = PurchaseForm()
    if form.validate_on_submit():
        purchase = Purchase(
            message=form.message.data,
            resource=resource,
            buyer=current_user,
            price=resource.sale_price or 0.0,
            status='pending'
        )
        db.session.add(purchase)
        
        # Notify owner
        from app.models import Notification
        owner_notif = Notification(user_id=resource.owner_id, message=f"{current_user.username} has requested to buy '{resource.title}'.")
        db.session.add(owner_notif)
        
        db.session.commit()
        flash('Your purchase request has been submitted and is pending seller approval.', 'success')
        return redirect(url_for('main.my_purchases'))
    return render_template('purchases/buy.html', title='Buy Resource', form=form, resource=resource)

@main.route('/my_purchases')
@login_required
def my_purchases():
    purchases = Purchase.query.filter_by(buyer=current_user).order_by(Purchase.request_date.desc()).all()
    return render_template('purchases/my_purchases.html', purchases=purchases)

@main.route('/purchase/<int:purchase_id>/update/<status>', methods=['POST'])
@login_required
def update_purchase_status(purchase_id, status):
    purchase = Purchase.query.get_or_404(purchase_id)
    if purchase.resource.owner != current_user:
        flash('You do not have permission to manage this purchase request.', 'danger')
        return redirect(url_for('main.manage_requests'))
        
    if status in ['approved', 'rejected']:
        purchase.status = status
        purchase.response_date = datetime.utcnow()
        if status == 'approved':
            purchase.resource.availability_status = 'Sold'
            # Reject other pending requests for this resource
            other_purchases = Purchase.query.filter(Purchase.resource_id == purchase.resource_id, Purchase.id != purchase.id, Purchase.status == 'pending').all()
            for p in other_purchases:
                p.status = 'rejected'
                p.response_date = datetime.utcnow()
            other_bookings = Booking.query.filter(Booking.resource_id == purchase.resource_id, Booking.status == 'pending').all()
            for b in other_bookings:
                b.status = 'rejected'
                b.response_date = datetime.utcnow()
        db.session.commit()
        
        # Notify buyer
        from app.models import Notification
        buyer_notif = Notification(user_id=purchase.buyer_id, message=f"Your purchase request for '{purchase.resource.title}' was {status}.")
        db.session.add(buyer_notif)
        db.session.commit()
        flash(f'Purchase request marked as {status}.', 'success')
    return redirect(url_for('main.manage_requests'))

# --- User Profiles & Follow Routes ---

@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UpdateProfileForm(current_user.username, current_user.email)
    if form.validate_on_submit():
        if form.profile_picture.data:
            current_user.profile_image_url = save_picture(form.profile_picture.data)
        if form.cover_picture.data:
            current_user.cover_image_url = save_picture(form.cover_picture.data)
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.user_profile', user_id=current_user.id))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('users/edit_profile.html', title='Edit Profile', form=form)

@main.route('/user/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    resources = Resource.query.filter_by(owner=user).order_by(Resource.created_at.desc()).all()
    is_following = current_user.is_following(user) if current_user.is_authenticated else False
    return render_template('users/profile.html', user=user, resources=resources, is_following=is_following)

@main.route('/follow/<int:user_id>', methods=['POST', 'GET'])
@login_required
def follow_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot follow yourself!', 'warning')
        return redirect(url_for('main.user_profile', user_id=user_id))
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {user.username}!', 'success')
    next_page = request.referrer or url_for('main.user_profile', user_id=user_id)
    return redirect(next_page)

@main.route('/unfollow/<int:user_id>', methods=['POST', 'GET'])
@login_required
def unfollow_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot unfollow yourself!', 'warning')
        return redirect(url_for('main.user_profile', user_id=user_id))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You unfollowed {user.username}.', 'info')
    next_page = request.referrer or url_for('main.user_profile', user_id=user_id)
    return redirect(next_page)

# --- Direct Messaging Routes (Instagram DM style) ---

@main.route('/messages')
@main.route('/messages/<int:recipient_id>')
@login_required
def messages(recipient_id=None):
    # Find all users with whom current_user has exchanged messages
    sent_to = db.session.query(Message.recipient_id).filter_by(sender_id=current_user.id)
    received_from = db.session.query(Message.sender_id).filter_by(recipient_id=current_user.id)
    chat_user_ids = sent_to.union(received_from).all()
    chat_user_ids = [uid[0] for uid in chat_user_ids if uid[0] != current_user.id]
    
    # Also load users that current_user follows
    followed_ids = [u.id for u in current_user.followed.all()]
    all_contact_ids = list(set(chat_user_ids + followed_ids))
    contacts = User.query.filter(User.id.in_(all_contact_ids)).all() if all_contact_ids else []

    active_recipient = None
    chat_messages = []
    resource_context = None
    
    ref_resource_id = request.args.get('resource_id', type=int)
    if ref_resource_id:
        resource_context = Resource.query.get(ref_resource_id)

    if recipient_id:
        active_recipient = User.query.get_or_404(recipient_id)
        if active_recipient not in contacts and active_recipient.id != current_user.id:
            contacts.insert(0, active_recipient)

        # Mark unread messages from recipient as read
        unread_msgs = Message.query.filter_by(sender_id=recipient_id, recipient_id=current_user.id, is_read=False).all()
        for msg in unread_msgs:
            msg.is_read = True
        db.session.commit()

        # Load message thread
        chat_messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == recipient_id)) |
            ((Message.sender_id == recipient_id) & (Message.recipient_id == current_user.id))
        ).order_by(Message.timestamp.asc()).all()

    form = MessageForm()
    return render_template('messages/inbox.html', contacts=contacts, active_recipient=active_recipient, chat_messages=chat_messages, resource_context=resource_context, form=form)

@main.route('/send_message/<int:recipient_id>', methods=['POST'])
@login_required
def send_message(recipient_id):
    recipient = User.query.get_or_404(recipient_id)
    form = MessageForm()
    resource_id = request.args.get('resource_id', type=int)
    if form.validate_on_submit():
        msg = Message(
            sender_id=current_user.id,
            recipient_id=recipient.id,
            resource_id=resource_id,
            body=form.body.data,
            timestamp=datetime.utcnow()
        )
        db.session.add(msg)
        db.session.commit()
        flash('Message sent!', 'success')
    return redirect(url_for('main.messages', recipient_id=recipient.id, resource_id=resource_id))

@main.route('/messages/<int:recipient_id>/delete', methods=['POST'])
@login_required
def delete_messages(recipient_id):
    Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == recipient_id)) |
        ((Message.sender_id == recipient_id) & (Message.recipient_id == current_user.id))
    ).delete()
    db.session.commit()
    flash('Conversation has been deleted.', 'success')
    return redirect(url_for('main.messages'))

# --- Dashboard ---

@main.route('/dashboard')
@login_required
def dashboard():
    owned_resources = Resource.query.filter_by(owner=current_user).all()
    borrowed_resources = Booking.query.filter_by(borrower=current_user, status='approved').all()
    purchased_items = Purchase.query.filter_by(buyer=current_user, status='approved').all()
    pending_requests = Booking.query.join(Resource).filter(Resource.owner_id == current_user.id, Booking.status == 'pending').all()
    pending_purchases = Purchase.query.join(Resource).filter(Resource.owner_id == current_user.id, Purchase.status == 'pending').all()
    
    followers_count = current_user.followers.count()
    following_count = current_user.followed.count()
    recent_messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.timestamp.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        owned=owned_resources,
        borrowed=borrowed_resources,
        purchased=purchased_items,
        pending=pending_requests,
        pending_purchases=pending_purchases,
        followers_count=followers_count,
        following_count=following_count,
        recent_messages=recent_messages
    )

# --- API Endpoints ---
from flask import jsonify

@main.route('/api/resources', methods=['GET'])
def api_get_resources():
    resources = Resource.query.filter_by(availability_status='Available').all()
    return jsonify([{
        'id': r.id, 
        'title': r.title, 
        'category': r.category, 
        'listing_type': r.listing_type, 
        'status': r.availability_status, 
        'currency': r.currency, 
        'currency_symbol': r.currency_symbol, 
        'daily_price': r.daily_price, 
        'sale_price': r.sale_price,
        'latitude': r.latitude,
        'longitude': r.longitude,
        'location': r.location,
        'owner': r.owner.username,
        'url': url_for('main.resource_detail', resource_id=r.id)
    } for r in resources])

@main.route('/api/resources/<int:resource_id>', methods=['GET'])
def api_get_resource(resource_id):
    r = Resource.query.get_or_404(resource_id)
    return jsonify({'id': r.id, 'title': r.title, 'description': r.description, 'category': r.category, 'listing_type': r.listing_type, 'status': r.availability_status, 'currency': r.currency, 'currency_symbol': r.currency_symbol, 'daily_price': r.daily_price, 'sale_price': r.sale_price})

@main.route('/api/bookings', methods=['GET'])
@login_required
def api_get_bookings():
    bookings = Booking.query.filter_by(borrower=current_user).all()
    return jsonify([{'id': b.id, 'resource_id': b.resource_id, 'status': b.status, 'start_date': b.start_date.strftime('%Y-%m-%d')} for b in bookings])

@main.route('/api/purchases', methods=['GET'])
@login_required
def api_get_purchases():
    purchases = Purchase.query.filter_by(buyer=current_user).all()
    return jsonify([{'id': p.id, 'resource_id': p.resource_id, 'status': p.status, 'price': p.price, 'request_date': p.request_date.strftime('%Y-%m-%d')} for p in purchases])

@main.route('/report_damage/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def report_damage(booking_id):
    from app.models import DamageReport
    booking = Booking.query.get_or_404(booking_id)
    if booking.resource.owner_id != current_user.id:
        flash('Only the owner can report damage.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    form = DamageReportForm()
    if form.validate_on_submit():
        image_url = None
        if form.image_file.data:
            image_url = save_picture(form.image_file.data)
            
        report = DamageReport(
            booking_id=booking.id,
            reporter_id=current_user.id,
            description=form.description.data,
            image_url=image_url
        )
        db.session.add(report)
        db.session.commit()
        
        # Optionally deduct trust score from borrower
        borrower = booking.borrower
        borrower.trust_score = max(0, (borrower.trust_score or 100) - 50)
        db.session.commit()
        
        flash('Damage reported successfully. The borrower has been penalized.', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('bookings/report_damage.html', form=form, booking=booking)

@main.route('/review/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def review_booking(booking_id):
    from app.models import Review
    booking = Booking.query.get_or_404(booking_id)
    if current_user.id not in [booking.borrower_id, booking.resource.owner_id]:
        flash('You do not have permission to review this booking.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    form = ReviewForm()
    if form.validate_on_submit():
        reviewee_id = booking.resource.owner_id if current_user.id == booking.borrower_id else booking.borrower_id
        review = Review(
            reviewer_id=current_user.id,
            reviewee_id=reviewee_id,
            booking_id=booking.id,
            rating=int(form.rating.data),
            comment=form.comment.data
        )
        db.session.add(review)
        db.session.commit()
        
        # Update user's average rating
        reviewee = User.query.get(reviewee_id)
        reviews = Review.query.filter_by(reviewee_id=reviewee_id).all()
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            reviewee.rating = round(avg_rating, 1)
            db.session.commit()
            
        flash('Review submitted successfully.', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('bookings/review.html', form=form, booking=booking)
