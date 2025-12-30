#!/usr/bin/env python3
"""Database migration script to create all tables"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database.database import engine, Base
from database import models  # Import all models

def migrate():
    """Create all database tables"""
    try:
        print("🔄 Creating database tables...")
        print(f"📍 Database URL: {engine.url}")

        # Create all tables
        Base.metadata.create_all(bind=engine)

        print("✅ Database tables created successfully!")
        print(f"📊 Created {len(Base.metadata.tables)} tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")

        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
