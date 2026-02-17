"""
SQLite-based per-user data storage for the Douban RAG system.

Stores chat messages and upload metadata so they persist across sessions.
"""

import sqlite3
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings


def _get_db_path() -> str:
    """Get the path to the user data database."""
    db_dir = os.path.dirname(settings.PERSIST_DIR)
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "chat_history.db")


def _get_connection() -> sqlite3.Connection:
    """Get a database connection with WAL mode for concurrency."""
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db():
    """Create tables if they don't exist."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_user_id
            ON messages(user_id)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS upload_status (
                user_id TEXT PRIMARY KEY,
                documents_processed INTEGER NOT NULL,
                media_types TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


# Initialize on module load
_init_db()


def save_message(user_id: str, role: str, content: str) -> int:
    """
    Save a chat message.

    Args:
        user_id: The authenticated user's ID
        role: 'user' or 'assistant'
        content: The message text

    Returns:
        The inserted row ID
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_messages(user_id: str, limit: int = 100) -> List[Dict]:
    """
    Get recent chat messages for a user, oldest first.

    Args:
        user_id: The authenticated user's ID
        limit: Max number of messages to return (default 100)

    Returns:
        List of message dicts with 'role', 'content', and 'created_at'
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT role, content, created_at FROM messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        # Reverse so oldest messages come first
        return [
            {"role": row["role"], "content": row["content"], "created_at": row["created_at"]}
            for row in reversed(rows)
        ]
    finally:
        conn.close()


def clear_messages(user_id: str) -> int:
    """
    Delete all chat messages for a user.

    Args:
        user_id: The authenticated user's ID

    Returns:
        Number of deleted rows
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM messages WHERE user_id = ?", (user_id,)
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def save_upload_status(user_id: str, documents_processed: int, media_types: dict) -> None:
    """
    Save or update the user's upload status.

    Args:
        user_id: The authenticated user's ID
        documents_processed: Number of documents indexed
        media_types: Dict of media type -> count (e.g. {"movie": 50, "book": 30})
    """
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO upload_status (user_id, documents_processed, media_types, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                documents_processed = excluded.documents_processed,
                media_types = excluded.media_types,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, documents_processed, json.dumps(media_types)),
        )
        conn.commit()
    finally:
        conn.close()


def get_upload_status(user_id: str) -> Optional[Dict]:
    """
    Get the user's upload status.

    Returns:
        Dict with 'documents_processed' and 'media_types', or None if no upload.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT documents_processed, media_types, updated_at FROM upload_status WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row:
            return {
                "documents_processed": row["documents_processed"],
                "media_types": json.loads(row["media_types"]),
                "updated_at": row["updated_at"],
            }
        return None
    finally:
        conn.close()

