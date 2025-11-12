# app/database/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.config import settings

# Create SQLite database engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
        "timeout": 20
    },
    echo=settings.DEBUG  # Log SQL queries in debug mode
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