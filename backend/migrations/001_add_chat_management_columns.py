"""
Migration: Add conversation management columns to Chat table

Adds the following columns to the chats table:
- archived_at (DateTime, nullable)
- archive_reason (String, nullable)
- last_activity_at (DateTime, default now)
- message_count (Integer, default 0)
- unread_count (Integer, default 0)
- auto_archive_after_days (Integer, default 90)
"""

import sys
sys.path.insert(0, '.')

from database.database import engine
from sqlalchemy import text
import os

def get_db_type():
    """Determine if we're using SQLite or PostgreSQL"""
    db_url = os.getenv('DATABASE_URL', '')
    if 'postgresql' in db_url or 'postgres' in db_url:
        return 'postgresql'
    return 'sqlite'

def run_migration():
    db_type = get_db_type()
    print(f"Running migration on {db_type} database...")

    with engine.connect() as conn:
        # Check if columns already exist
        try:
            result = conn.execute(text("SELECT archived_at FROM chats LIMIT 1"))
            print("✅ Columns already exist, skipping migration")
            return
        except Exception:
            print("Columns don't exist, proceeding with migration...")

        # Add columns based on database type
        migrations = []

        if db_type == 'postgresql':
            migrations = [
                "ALTER TABLE chats ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP",
                "ALTER TABLE chats ADD COLUMN IF NOT EXISTS archive_reason VARCHAR",
                "ALTER TABLE chats ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP DEFAULT NOW()",
                "ALTER TABLE chats ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0",
                "ALTER TABLE chats ADD COLUMN IF NOT EXISTS unread_count INTEGER DEFAULT 0",
                "ALTER TABLE chats ADD COLUMN IF NOT EXISTS auto_archive_after_days INTEGER DEFAULT 90"
            ]
        else:  # sqlite
            # SQLite doesn't support IF NOT EXISTS, need to check first
            # Also need to add columns one by one
            # SQLite doesn't support DEFAULT CURRENT_TIMESTAMP on ALTER TABLE, so we add without default
            migrations = [
                "ALTER TABLE chats ADD COLUMN archived_at TIMESTAMP",
                "ALTER TABLE chats ADD COLUMN archive_reason TEXT",
                "ALTER TABLE chats ADD COLUMN last_activity_at TIMESTAMP",
                "ALTER TABLE chats ADD COLUMN message_count INTEGER DEFAULT 0",
                "ALTER TABLE chats ADD COLUMN unread_count INTEGER DEFAULT 0",
                "ALTER TABLE chats ADD COLUMN auto_archive_after_days INTEGER DEFAULT 90"
            ]

        # Execute migrations
        for migration_sql in migrations:
            try:
                conn.execute(text(migration_sql))
                print(f"✅ Executed: {migration_sql[:60]}...")
            except Exception as e:
                # Column might already exist
                print(f"⚠️  Skipped (may already exist): {migration_sql[:60]}... - {e}")

        conn.commit()
        print("✅ Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
