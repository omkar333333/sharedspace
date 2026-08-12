from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app, send_file
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Resource, Booking, Purchase, Message
from app.forms import RegistrationForm, LoginForm, ResourceForm, BookingForm, PurchaseForm, MessageForm
from datetime import datetime
import qrcode
import io

main = Blueprint('main', __name__)

@main.app_context_processor
def inject_globals():
    if current_user.is_authenticated:
        return {'unread_count': current_user.unread_message_count()}
    return {'unread_count': 0}


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
    return render_template('resources/detail.html', title=resource.title, resource=resource)

@main.route('/resource/<int:resource_id>/qrcode')
def resource_qrcode(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    url = url_for('main.resource_detail', resource_id=resource.id, _external=True)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

@main.route('/resource/new', methods=['GET', 'POST'])
@login_required
def create_resource():
    form = ResourceForm()
    if form.validate_on_submit():
        resource = Resource(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            location=form.location.data,
            image_url=form.image_url.data,
            currency=form.currency.data,
            daily_price=form.daily_price.data,
            listing_type=form.listing_type.data,
            sale_price=form.sale_price.data,
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
        resource.title = form.title.data
        resource.description = form.description.data
        resource.category = form.category.data
        resource.location = form.location.data
        resource.image_url = form.image_url.data
        resource.currency = form.currency.data
        resource.daily_price = form.daily_price.data
        resource.listing_type = form.listing_type.data
        resource.sale_price = form.sale_price.data
        db.session.commit()
        flash('Your resource has been updated!', 'success')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
    elif request.method == 'GET':
        form.title.data = resource.title
        form.description.data = resource.description
        form.category.data = resource.category
        form.location.data = resource.location
        form.image_url.data = resource.image_url
        form.currency.data = resource.currency
        form.daily_price.data = resource.daily_price
        form.listing_type.data = resource.listing_type
        form.sale_price.data = resource.sale_price
    return render_template('resources/create.html', title='Update Resource', form=form, legend='Update Resource')

@main.route('/resource/<int:resource_id>/delete', methods=['POST'])
@login_required
def delete_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.owner != current_user:
        flash('You do not have permission to delete this resource', 'danger')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
    db.session.delete(resource)
    db.session.commit()
    flash('Your resource has been deleted!', 'success')
    return redirect(url_for('main.list_resources'))

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
    if resource.availability_status != 'Available':
        flash('This resource is currently not available for booking.', 'warning')
        return redirect(url_for('main.resource_detail', resource_id=resource.id))
        
    form = BookingForm()
    if form.validate_on_submit():
        booking = Booking(
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            purpose=form.purpose.data,
            resource=resource,
            borrower=current_user,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        flash('Your booking request has been submitted and is pending approval.', 'success')
        return redirect(url_for('main.my_bookings'))
    return render_template('bookings/request.html', title='Book Resource', form=form, resource=resource)

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
        flash(f'Purchase request marked as {status}.', 'success')
    return redirect(url_for('main.manage_requests'))

# --- User Profiles & Follow Routes ---

@main.route('/user/<int:user_id>')
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
    resources = Resource.query.all()
    return jsonify([{'id': r.id, 'title': r.title, 'category': r.category, 'listing_type': r.listing_type, 'status': r.availability_status, 'currency': r.currency, 'currency_symbol': r.currency_symbol, 'daily_price': r.daily_price, 'sale_price': r.sale_price} for r in resources])

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



