"""
Main migration runner - executes all pending migrations
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.database import engine
from sqlalchemy import text

def get_db_type():
    """Determine if we're using SQLite or PostgreSQL"""
    db_url = os.getenv('DATABASE_URL', '')
    if 'postgresql' in db_url or 'postgres' in db_url:
        return 'postgresql'
    return 'sqlite'

def run_all_migrations():
    """Run all database migrations"""
    db_type = get_db_type()
    print(f"🔧 Running migrations on {db_type} database...")

    with engine.connect() as conn:
        # Chat table migrations
        print("📋 Migrating chats table...")
        chat_columns = [
            ('archived_at', 'TIMESTAMP'),
            ('archive_reason', 'VARCHAR' if db_type == 'postgresql' else 'TEXT'),
            ('last_activity_at', 'TIMESTAMP'),
            ('message_count', 'INTEGER DEFAULT 0'),
            ('unread_count', 'INTEGER DEFAULT 0'),
            ('extra_data', 'JSONB' if db_type == 'postgresql' else 'TEXT'),
            ('auto_archive_after_days', 'INTEGER DEFAULT 90'),
        ]

        for col_name, col_type in chat_columns:
            try:
                if db_type == 'postgresql':
                    conn.execute(text(f'ALTER TABLE chats ADD COLUMN IF NOT EXISTS {col_name} {col_type}'))
                else:
                    conn.execute(text(f'ALTER TABLE chats ADD COLUMN {col_name} {col_type}'))
                conn.commit()
                print(f'  ✅ {col_name}')
            except Exception as e:
                error_msg = str(e).lower()
                if 'duplicate' in error_msg or 'already exists' in error_msg:
                    print(f'  ⚠️  {col_name} exists')
                else:
                    print(f'  ❌ {col_name}: {e}')

        # Message table migrations
        print("📨 Migrating messages table...")
        message_columns = [
            ('archived_at', 'TIMESTAMP'),
            ('archive_reason', 'VARCHAR' if db_type == 'postgresql' else 'TEXT'),
            ('processed', 'BOOLEAN DEFAULT FALSE' if db_type == 'postgresql' else 'INTEGER DEFAULT 0'),
            ('read_at', 'TIMESTAMP'),
            ('extra_data', 'JSONB' if db_type == 'postgresql' else 'TEXT'),
            ('last_synced_at', 'TIMESTAMP'),
            ('sentiment', 'VARCHAR' if db_type == 'postgresql' else 'TEXT'),
            ('category', 'VARCHAR' if db_type == 'postgresql' else 'TEXT'),
            ('tags', 'TEXT[]' if db_type == 'postgresql' else 'TEXT'),
        ]

        for col_name, col_type in message_columns:
            try:
                if db_type == 'postgresql':
                    conn.execute(text(f'ALTER TABLE messages ADD COLUMN IF NOT EXISTS {col_name} {col_type}'))
                else:
                    conn.execute(text(f'ALTER TABLE messages ADD COLUMN {col_name} {col_type}'))
                conn.commit()
                print(f'  ✅ {col_name}')
            except Exception as e:
                error_msg = str(e).lower()
                if 'duplicate' in error_msg or 'already exists' in error_msg:
                    print(f'  ⚠️  {col_name} exists')
                else:
                    print(f'  ❌ {col_name}: {e}')

        print("✅ All migrations completed!")

if __name__ == "__main__":
    run_all_migrations()
