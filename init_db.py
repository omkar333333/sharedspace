from app import create_app, db

app = create_app()

from sqlalchemy import text

with app.app_context():
    db.create_all()
    
    # Safely add latitude and longitude columns to production database
    try:
        db.session.execute(text("ALTER TABLE resource ADD COLUMN latitude FLOAT"))
        db.session.commit()
    except Exception:
        db.session.rollback()
        pass

    try:
        db.session.execute(text("ALTER TABLE resource ADD COLUMN longitude FLOAT"))
        db.session.commit()
    except Exception:
        db.session.rollback()
        pass
        
    print("Database tables created/updated successfully!")
