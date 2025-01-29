import sqlite3
from contextlib import closing
from config import SQLITE_DB_PATH

def init_db():
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    subscription_status TEXT DEFAULT 'inactive',
                    subscription_expires_at TEXT
                )
            ''')

def add_user_if_not_exists(user_id: int, username: str):
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO users (user_id, username) VALUES (?, ?)",
                    (user_id, username)
                )

def user_has_active_subscription(user_id: int) -> bool:
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute("SELECT subscription_status FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                return row[0] == 'active'
            return False

def activate_subscription(user_id: int):
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute(
                "UPDATE users SET subscription_status = 'active', subscription_expires_at = datetime('now', '+30 days') WHERE user_id = ?",
                (user_id,)
            )

def deactivate_subscription(user_id: int):
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute(
                "UPDATE users SET subscription_status = 'inactive', subscription_expires_at = NULL WHERE user_id = ?",
                (user_id,)
            )