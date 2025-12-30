"""Admin endpoints for maintenance tasks"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import os

from database.database import engine

router = APIRouter()

@router.post("/run-migrations")
async def run_migrations():
    """Manually trigger database migrations"""
    try:
        db_url = os.getenv('DATABASE_URL', '')
        db_type = 'postgresql' if 'postgresql' in db_url or 'postgres' in db_url else 'sqlite'

        print(f"🔧 Running migrations on {db_type}...")
        results = []

        with engine.connect() as conn:
            # Chat table migrations
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
                    results.append(f"✅ chats.{col_name}")
                except Exception as e:
                    if 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                        results.append(f"⚠️  chats.{col_name} exists")
                    else:
                        results.append(f"❌ chats.{col_name}: {str(e)}")

            # Message table migrations
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
                    results.append(f"✅ messages.{col_name}")
                except Exception as e:
                    if 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                        results.append(f"⚠️  messages.{col_name} exists")
                    else:
                        results.append(f"❌ messages.{col_name}: {str(e)}")

        return {
            "success": True,
            "db_type": db_type,
            "results": results,
            "message": "Migrations completed"
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}\n{error_details}")
