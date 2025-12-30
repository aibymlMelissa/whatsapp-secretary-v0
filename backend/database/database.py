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
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()