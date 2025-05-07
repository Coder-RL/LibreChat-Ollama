# scripts/init_database.py

from app.models.database import db

if __name__ == "__main__":
    print("🔄 Initializing database...")
    db.initialize()
    print("✅ Database initialized successfully.")
