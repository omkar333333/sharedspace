from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    db.create_all()
    try:
        db.session.execute(text("ALTER TABLE resource ADD COLUMN latitude FLOAT"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE resource ADD COLUMN longitude FLOAT"))
        db.session.commit()
    except Exception:
        db.session.rollback()

if __name__ == '__main__':
    app.run(debug=True)
