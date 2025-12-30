# app/database/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, NullPool

from core.config import settings

# Configure engine based on database type
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # SQLite configuration
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        echo=settings.DEBUG
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,
        max_overflow=20,
        echo=settings.DEBUG
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import Base from separate file to avoid circular imports
from database.base import Base

# Export Base for backward compatibility
__all__ = ['Base', 'get_db', 'init_db']

async def init_db():
    """Initialize database tables"""
    try:
        print(f"🔄 Initializing database...")
        print(f"📍 Database URL: {str(engine.url).split('@')[0]}@***")  # Hide password

        # Import all models to ensure they're registered
        from database import models

        # Create all tables (sync operation)
        Base.metadata.create_all(bind=engine)

        print(f"✅ Database tables created successfully!")
        print(f"📊 Total tables: {len(Base.metadata.tables)}")
        for table_name in list(Base.metadata.tables.keys())[:5]:  # Show first 5
            print(f"   - {table_name}")
        if len(Base.metadata.tables) > 5:
            print(f"   ... and {len(Base.metadata.tables) - 5} more")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        raise

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()