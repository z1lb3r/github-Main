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
                    full_name TEXT,
                    birth_date TEXT,         -- формат: ГГГГ-ММ-ДД
                    birth_time TEXT,         -- формат: ЧЧ:ММ
                    birth_latitude REAL,
                    birth_longitude REAL,
                    birth_altitude REAL,
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

def update_user_profile(user_id: int, full_name: str, birth_date: str, birth_time: str, latitude: float, longitude: float, altitude: float):
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute(
                """UPDATE users 
                   SET full_name = ?, birth_date = ?, birth_time = ?,
                       birth_latitude = ?, birth_longitude = ?, birth_altitude = ?
                   WHERE user_id = ?""",
                (full_name, birth_date, birth_time, latitude, longitude, altitude, user_id)
            )

def get_user_profile(user_id: int) -> dict:
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute(
                """SELECT full_name, birth_date, birth_time, birth_latitude, birth_longitude, birth_altitude 
                   FROM users WHERE user_id = ?""",
                (user_id,)
            ).fetchone()
            if row and all(row):
                return {
                    "full_name": row[0],
                    "birth_date": row[1],
                    "birth_time": row[2],
                    "latitude": row[3],
                    "longitude": row[4],
                    "altitude": row[5]
                }
            return {}

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
