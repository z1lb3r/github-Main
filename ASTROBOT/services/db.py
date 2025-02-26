"""
Сервис для работы с базой данных SQLite.
Содержит функции для инициализации БД, управления пользователями и подписками.
"""

import sqlite3
from contextlib import closing
from config import SQLITE_DB_PATH

def init_db():
    """
    Инициализирует базу данных SQLite.
    Создает таблицу пользователей, если она еще не существует.
    """
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
    """
    Добавляет пользователя в БД, если он еще не существует.
    
    Args:
        user_id (int): ID пользователя в Telegram
        username (str): Имя пользователя в Telegram
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO users (user_id, username) VALUES (?, ?)",
                    (user_id, username)
                )

def update_user_profile(user_id: int, full_name: str, birth_date: str, birth_time: str, latitude: float, longitude: float, altitude: float):
    """
    Обновляет профиль пользователя в БД.
    
    Args:
        user_id (int): ID пользователя
        full_name (str): Полное имя пользователя
        birth_date (str): Дата рождения (ГГГГ-ММ-ДД)
        birth_time (str): Время рождения (ЧЧ:ММ)
        latitude (float): Широта места рождения
        longitude (float): Долгота места рождения
        altitude (float): Высота места рождения
    """
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
    """
    Получает профиль пользователя из БД.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        dict: Словарь с данными пользователя или пустой словарь, если профиль не заполнен
    """
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
    """
    Проверяет, есть ли у пользователя активная подписка.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        bool: True, если подписка активна, иначе False
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute("SELECT subscription_status FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                return row[0] == 'active'
            return False

def activate_subscription(user_id: int):
    """
    Активирует подписку для пользователя на 30 дней.
    
    Args:
        user_id (int): ID пользователя
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute(
                "UPDATE users SET subscription_status = 'active', subscription_expires_at = datetime('now', '+30 days') WHERE user_id = ?",
                (user_id,)
            )

def deactivate_subscription(user_id: int):
    """
    Деактивирует подписку пользователя.
    
    Args:
        user_id (int): ID пользователя
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute(
                "UPDATE users SET subscription_status = 'inactive', subscription_expires_at = NULL WHERE user_id = ?",
                (user_id,)
            )