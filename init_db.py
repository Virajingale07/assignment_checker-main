# File: init_db.py
# File: init_db.py
from app import create_app, db

def init_database():
    app = create_app()
    with app.app_context():
        try:
            # REMOVED db.drop_all()
            print("Checking database tables...")
            db.create_all() # This creates tables ONLY if they don't exist
            print("✅ Database is ready and persistent.")
        except Exception as e:
            print(f"⚠️ Database error: {e}")

if __name__ == "__main__":
    init_database()