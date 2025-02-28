"""
Сервис для работы с базой данных SQLite.
Содержит функции для инициализации БД, управления пользователями и балансом в USD.
"""

import sqlite3
from contextlib import closing
from config import SQLITE_DB_PATH

def init_db():
    """
    Инициализирует базу данных SQLite.
    Создает таблицу пользователей, если она еще не существует.
    Добавляет поле balance, если оно отсутствует.
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Создаем основную таблицу пользователей
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
                    subscription_expires_at TEXT,
                    balance REAL DEFAULT 0.0  -- Баланс пользователя в USD
                )
            ''')
            
            # Проверяем, есть ли столбец balance, и добавляем его, если отсутствует
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'balance' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0")
                print("Добавлен столбец 'balance' в таблицу 'users'")
            
            # Создаем таблицу для хранения истории транзакций
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,            -- Сумма в USD
                    type TEXT,              -- 'deposit' или 'charge'
                    description TEXT,
                    original_currency TEXT, -- Валюта, в которой был сделан платеж
                    original_amount REAL,   -- Сумма в исходной валюте
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Проверяем наличие новых столбцов в таблице transactions
            cursor.execute("PRAGMA table_info(transactions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'original_currency' not in columns and 'id' in columns:
                conn.execute("ALTER TABLE transactions ADD COLUMN original_currency TEXT DEFAULT 'USD'")
                print("Добавлен столбец 'original_currency' в таблицу 'transactions'")
                
            if 'original_amount' not in columns and 'id' in columns:
                conn.execute("ALTER TABLE transactions ADD COLUMN original_amount REAL DEFAULT 0.0")
                print("Добавлен столбец 'original_amount' в таблицу 'transactions'")

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
                    "INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                    (user_id, username, 0.0)
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
                """SELECT full_name, birth_date, birth_time, birth_latitude, birth_longitude, birth_altitude, balance 
                   FROM users WHERE user_id = ?""",
                (user_id,)
            ).fetchone()
            if row and all(row[:6]):  # Проверяем, что все основные поля заполнены
                return {
                    "full_name": row[0],
                    "birth_date": row[1],
                    "birth_time": row[2],
                    "latitude": row[3],
                    "longitude": row[4],
                    "altitude": row[5],
                    "balance": row[6] if row[6] is not None else 0.0
                }
            return {}

def get_user_balance(user_id: int) -> float:
    """
    Получает текущий баланс пользователя в USD.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        float: Баланс пользователя или 0.0, если пользователь не найден
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                return float(row[0]) if row[0] is not None else 0.0
            return 0.0

def add_to_balance(user_id: int, amount: float, description: str = "Пополнение баланса", original_currency: str = "USD", original_amount: float = None):
    """
    Добавляет средства на баланс пользователя в USD.
    
    Args:
        user_id (int): ID пользователя
        amount (float): Сумма для добавления в USD
        description (str, optional): Описание транзакции
        original_currency (str, optional): Исходная валюта платежа
        original_amount (float, optional): Сумма в исходной валюте
    
    Returns:
        float: Новый баланс пользователя
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Если не указана оригинальная сумма, используем сумму в USD
            if original_amount is None:
                original_amount = amount
                
            # Добавляем средства на баланс
            conn.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (amount, user_id)
            )
            
            # Записываем транзакцию
            conn.execute(
                "INSERT INTO transactions (user_id, amount, type, description, original_currency, original_amount) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, amount, "deposit", description, original_currency, original_amount)
            )
            
            # Получаем обновленный баланс
            row = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                return float(row[0])
            return 0.0

def subtract_from_balance(user_id: int, amount: float, description: str = "Списание за использование бота") -> bool:
    """
    Списывает средства с баланса пользователя в USD, если их достаточно.
    
    Args:
        user_id (int): ID пользователя
        amount (float): Сумма для списания в USD
        description (str, optional): Описание транзакции
    
    Returns:
        bool: True, если списание прошло успешно, False, если недостаточно средств
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Проверяем, достаточно ли средств
            row = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if not row or float(row[0]) < amount:
                return False
            
            # Списываем средства
            conn.execute(
                "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                (amount, user_id)
            )
            
            # Записываем транзакцию (отрицательная сумма)
            conn.execute(
                "INSERT INTO transactions (user_id, amount, type, description, original_currency, original_amount) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, -amount, "charge", description, "USD", -amount)
            )
            
            return True

def get_transaction_history(user_id: int, limit: int = 10) -> list:
    """
    Получает историю транзакций пользователя.
    
    Args:
        user_id (int): ID пользователя
        limit (int, optional): Максимальное количество транзакций
    
    Returns:
        list: Список транзакций
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row  # Для доступа к строкам по имени столбца
        with conn:
            rows = conn.execute(
                """SELECT id, amount, type, description, created_at, original_currency, original_amount
                   FROM transactions 
                   WHERE user_id = ? 
                   ORDER BY created_at DESC 
                   LIMIT ?""",
                (user_id, limit)
            ).fetchall()
            
            return [dict(row) for row in rows]

def user_has_active_subscription(user_id: int) -> bool:
    """
    Проверяет, есть ли у пользователя активная подписка.
    В новой модели этот метод проверяет, есть ли у пользователя достаточно средств.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        bool: True, если у пользователя есть средства, иначе False
    """
    balance = get_user_balance(user_id)
    return balance > 0

def activate_subscription(user_id: int):
    """
    Устаревший метод для обратной совместимости.
    В новой модели используйте add_to_balance.
    """
    # Ничего не делаем, оставляем для обратной совместимости
    pass

def deactivate_subscription(user_id: int):
    """
    Устаревший метод для обратной совместимости.
    В новой модели это обнуление баланса пользователя.
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute(
                "UPDATE users SET balance = 0 WHERE user_id = ?",
                (user_id,)
            )