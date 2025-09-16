# app/database/database.py
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from core.config import settings

# Create sync database engine for compatibility
engine = create_engine(
    settings.DATABASE_URL.replace('asyncpg://', 'postgresql://'),
    echo=True,  # Set to False in production
)

# Create async database engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to False in production
)

# Create async session maker
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Import Base from separate file to avoid circular imports
from database.base import Base

# Export Base for backward compatibility
__all__ = ['Base', 'get_db', 'init_db']

async def init_db():
    """Initialize database tables"""
    async with async_engine.begin() as conn:
        # Import all models to ensure they are registered with Base
        from database import models

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully")

async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()