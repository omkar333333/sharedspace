from app import create_app, db
from app.models import User, Resource, Purchase, Booking
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

app = create_app()

def seed_data():
    with app.app_context():
        # Clean up existing data if any
        db.drop_all()
        db.create_all()

        print("Creating sample users...")
        users = [
            User(username='Alex Morgan', email='alex@example.com', password_hash=generate_password_hash('password123'), rating=4.8),
            User(username='Sam Lee', email='sam@example.com', password_hash=generate_password_hash('password123'), rating=4.9),
            User(username='Mia Patel', email='mia@example.com', password_hash=generate_password_hash('password123'), rating=5.0)
        ]
        db.session.add_all(users)
        db.session.commit()

        print("Creating sample resources...")
        resources = [
            Resource(
                title='Arduino Uno Starter Kit',
                description='Complete starter kit with breadboard, LEDs, resistors, jumper wires, and motors.',
                category='Electronics',
                location='Engineering Building',
                image_url='/static/img/arduino.jpg',
                currency='USD',
                daily_price=2.00,
                listing_type='Rent',
                availability_status='Available',
                owner=users[0]
            ),
            Resource(
                title='3D Printer (Ender 3 V2)',
                description='Great for small rapid prototyping projects. Filament not included. Up for sale or rent.',
                category='Equipment',
                location='Makerspace',
                image_url='/static/img/printer.jpg',
                currency='EUR',
                daily_price=15.00,
                listing_type='Both',
                sale_price=180.00,
                availability_status='Available',
                owner=users[1]
            ),
            Resource(
                title='Introduction to Algorithms',
                description='Classic CLRS textbook, 3rd Edition. Selling textbook in great condition.',
                category='Books',
                location='Library Café',
                image_url='/static/img/books.jpg',
                currency='INR',
                daily_price=0.00,
                listing_type='Sale',
                sale_price=3500.00,
                availability_status='Available',
                owner=users[2]
            ),
            Resource(
                title='Digital Multimeter',
                description='Fluke 117 Electricians True RMS Multimeter. Very accurate. Includes test leads.',
                category='Tools',
                location='Engineering Building Lab 2',
                image_url='/static/img/multimeter.jpg',
                currency='GBP',
                daily_price=0.00,
                listing_type='Rent',
                availability_status='Borrowed',
                owner=users[1]
            ),
            Resource(
                title='Raspberry Pi 4 (8GB)',
                description='Barely used Raspberry Pi 4 with 8GB RAM. Comes with power supply, case, and 32GB SD Card.',
                category='Electronics',
                location='Dorm A, Room 101',
                image_url='/static/img/pi.jpg',
                currency='USD',
                daily_price=5.00,
                listing_type='Both',
                sale_price=65.00,
                availability_status='Available',
                owner=users[0]
            ),
            Resource(
                title='Calculus Early Transcendentals',
                description='8th Edition calculus textbook. Sold to campus student.',
                category='Books',
                location='Science Quad',
                image_url='/static/img/books.jpg',
                currency='USD',
                daily_price=0.00,
                listing_type='Sale',
                sale_price=35.00,
                availability_status='Sold',
                owner=users[0]
            )
        ]
        
        db.session.add_all(resources)
        db.session.commit()
        
        print("Creating follow relationships...")
        users[0].follow(users[1]) # Alex follows Sam
        users[0].follow(users[2]) # Alex follows Mia
        users[1].follow(users[0]) # Sam follows Alex
        users[2].follow(users[0]) # Mia follows Alex
        db.session.commit()

        print("Creating sample purchases & bookings...")
        sample_purchase = Purchase(
            message='Hi! I would like to buy your Raspberry Pi 4 kit for my robotics project.',
            status='pending',
            price=65.00,
            resource=resources[4], # Raspberry Pi
            buyer=users[2] # Mia Patel
        )
        sample_sold_purchase = Purchase(
            message='Will buy the calculus book today!',
            status='approved',
            price=35.00,
            response_date=datetime.utcnow(),
            resource=resources[5], # Calculus Book
            buyer=users[1] # Sam Lee
        )
        
        db.session.add_all([sample_purchase, sample_sold_purchase])
        db.session.commit()

        print("Creating sample messages...")
        from app.models import Message
        sample_messages = [
            Message(sender_id=users[2].id, recipient_id=users[0].id, resource_id=resources[4].id, body='Hi Alex! Is the Raspberry Pi 4 still available for pickup today?', timestamp=datetime.utcnow() - timedelta(hours=2), is_read=False),
            Message(sender_id=users[0].id, recipient_id=users[2].id, resource_id=resources[4].id, body='Hey Mia! Yes, it is! I can meet you at the Engineering Building around 3 PM.', timestamp=datetime.utcnow() - timedelta(hours=1), is_read=True),
            Message(sender_id=users[1].id, recipient_id=users[0].id, resource_id=resources[0].id, body='Hey Alex, do you have extra jumper wires included with the Arduino kit?', timestamp=datetime.utcnow() - timedelta(minutes=30), is_read=False)
        ]
        db.session.add_all(sample_messages)
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_data()

