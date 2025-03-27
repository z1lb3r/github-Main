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
    print(f"Инициализация базы данных: {SQLITE_DB_PATH}")
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
            print("Таблица users создана или уже существует")
            
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
            print("Таблица transactions создана или уже существует")
            
            # Создаем таблицу для хранения реферальных связей
            conn.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    referrer_id INTEGER,
                    status TEXT DEFAULT 'pending',  -- 'pending', 'active', 'paid'
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    activated_at DATETIME,
                    reward_amount REAL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (referrer_id) REFERENCES users (user_id)
                )
            ''')
            print("Таблица referrals создана или уже существует")
            
            # Создаем таблицу для хранения сообщений
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    sender TEXT,     -- 'user' или 'bot' или 'summary'
                    content TEXT,
                    is_summary BOOLEAN DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            print("Таблица messages создана или уже существует")
            
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
    print(f"Проверяем наличие пользователя {user_id} ({username}) в БД")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row is None:
                print(f"Пользователь {user_id} не найден, добавляем в БД")
                conn.execute(
                    "INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                    (user_id, username, 0.0)
                )
                print(f"Пользователь {user_id} добавлен в БД")
            else:
                print(f"Пользователь {user_id} уже существует в БД")

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
    print(f"Обновляем профиль пользователя {user_id}:")
    print(f"Имя: {full_name}, Дата: {birth_date}, Время: {birth_time}, Координаты: {latitude}, {longitude}, {altitude}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Сначала проверим, существует ли пользователь
            check = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if not check:
                print(f"ОШИБКА: Пользователь {user_id} не найден в БД для обновления профиля")
                # Создадим пользователя, если он не существует
                conn.execute(
                    "INSERT INTO users (user_id, username) VALUES (?, ?)",
                    (user_id, f"user_{user_id}")
                )
                print(f"Пользователь {user_id} был автоматически создан")
                
            # Обновляем профиль
            conn.execute(
                """UPDATE users 
                   SET full_name = ?, birth_date = ?, birth_time = ?,
                       birth_latitude = ?, birth_longitude = ?, birth_altitude = ?
                   WHERE user_id = ?""",
                (full_name, birth_date, birth_time, latitude, longitude, altitude, user_id)
            )
            print(f"Профиль пользователя {user_id} обновлен в БД")
            
            # Проверяем, что данные действительно обновились
            row = conn.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,)).fetchone()
            print(f"Проверка обновления: full_name = {row[0] if row else 'Нет данных'}")

def get_user_profile(user_id: int) -> dict:
    """
    Получает профиль пользователя из БД.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        dict: Словарь с данными пользователя или пустой словарь, если профиль не заполнен
    """
    print(f"Запрашиваем профиль для user_id={user_id}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Проверяем, существует ли пользователь
            exists_query = "SELECT 1 FROM users WHERE user_id = ?"
            user_exists = conn.execute(exists_query, (user_id,)).fetchone()
            print(f"Пользователь существует в БД: {user_exists is not None}")
            
            if not user_exists:
                print(f"Пользователь {user_id} не найден в БД")
                return {}
            
            # Получаем данные пользователя
            query = """SELECT full_name, birth_date, birth_time, birth_latitude, birth_longitude, birth_altitude, balance 
                       FROM users WHERE user_id = ?"""
            row = conn.execute(query, (user_id,)).fetchone()
            print(f"Получены данные пользователя: {row}")
            
            # Если запись существует, возвращаем словарь
            if row:
                # Проверяем основной индикатор заполненности профиля - имя
                if not row[0]:
                    print(f"Имя пользователя {user_id} не заполнено, считаем профиль пустым")
                    return {}
                    
                result = {
                    "full_name": row[0],
                    "birth_date": row[1] or "",
                    "birth_time": row[2] or "",
                    "latitude": row[3] if row[3] is not None else 0.0,
                    "longitude": row[4] if row[4] is not None else 0.0,
                    "altitude": row[5] if row[5] is not None else 0.0,
                    "balance": row[6] if row[6] is not None else 0.0
                }
                print(f"Возвращаем результат: {result}")
                return result
            
            print("Строка не найдена, возвращаем пустой словарь")
            return {}

def get_user_balance(user_id: int) -> float:
    """
    Получает текущий баланс пользователя в баллах (рублях).
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        float: Баланс пользователя или 0.0, если пользователь не найден
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                balance = float(row[0]) if row[0] is not None else 0.0
                print(f"Баланс пользователя {user_id}: {balance:.0f} баллов")
                return balance
            print(f"Пользователь {user_id} не найден, возвращаем баланс 0.0")
            return 0.0

def add_to_balance(user_id: int, amount: float, description: str = "Пополнение баланса", original_currency: str = "RUB", original_amount: float = None):
    """
    Добавляет средства на баланс пользователя в баллах (рублях).
    
    Args:
        user_id (int): ID пользователя
        amount (float): Сумма для добавления в баллах
        description (str, optional): Описание транзакции
        original_currency (str, optional): Исходная валюта платежа
        original_amount (float, optional): Сумма в исходной валюте
    
    Returns:
        float: Новый баланс пользователя
    """
    print(f"Пополнение баланса пользователя {user_id} на {amount:.0f} баллов ({description})")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Если не указана оригинальная сумма, используем сумму в баллах
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
                new_balance = float(row[0])
                print(f"Новый баланс пользователя {user_id}: {new_balance:.0f} баллов")
                return new_balance
            print(f"ОШИБКА: Пользователь {user_id} не найден после пополнения баланса")
            return 0.0

def subtract_from_balance(user_id: int, amount: float, description: str = "Списание за использование бота") -> bool:
    """
    Списывает средства с баланса пользователя в баллах, если их достаточно.
    
    Args:
        user_id (int): ID пользователя
        amount (float): Сумма для списания в баллах
        description (str, optional): Описание транзакции
    
    Returns:
        bool: True, если списание прошло успешно, False, если недостаточно средств
    """
    print(f"Списание с баланса пользователя {user_id}: {amount:.2f} баллов ({description})")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Проверяем, достаточно ли средств
            row = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if not row:
                print(f"ОШИБКА: Пользователь {user_id} не найден при попытке списания")
                return False
                
            current_balance = float(row[0]) if row[0] is not None else 0.0
            
            if current_balance < amount:
                print(f"Недостаточно средств: баланс {current_balance:.2f} баллов, требуется {amount:.2f} баллов")
                return False
            
            # Списываем средства
            conn.execute(
                "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                (amount, user_id)
            )
            
            # Записываем транзакцию (отрицательная сумма)
            conn.execute(
                "INSERT INTO transactions (user_id, amount, type, description, original_currency, original_amount) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, -amount, "charge", description, "RUB", -amount)
            )
            
            # Получаем обновленный баланс для проверки
            new_balance = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
            print(f"Списание успешно. Новый баланс: {new_balance:.2f} баллов")
            
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
    print(f"Запрос истории транзакций пользователя {user_id} (лимит: {limit})")
    
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
            
            result = [dict(row) for row in rows]
            print(f"Получено {len(result)} транзакций")
            return result

def user_has_active_subscription(user_id: int) -> bool:
    """
    Проверяет, есть ли у пользователя активная подписка.
    В новой модели этот метод проверяет, есть ли у пользователя достаточно средств.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        bool: True, если у пользователя есть средства, иначе False
    """
    from config import MIN_REQUIRED_BALANCE
    balance = get_user_balance(user_id)
    has_subscription = balance >= MIN_REQUIRED_BALANCE
    print(f"Проверка подписки пользователя {user_id}: {has_subscription} (баланс: {balance:.0f} баллов, мин. баланс: {MIN_REQUIRED_BALANCE:.0f} баллов)")
    return has_subscription

def activate_subscription(user_id: int):
    """
    Устаревший метод для обратной совместимости.
    В новой модели используйте add_to_balance.
    """
    print(f"УСТАРЕВШИЙ МЕТОД: activate_subscription вызван для пользователя {user_id}")
    # Ничего не делаем, оставляем для обратной совместимости
    pass

def deactivate_subscription(user_id: int):
    """
    Устаревший метод для обратной совместимости.
    В новой модели это обнуление баланса пользователя.
    """
    print(f"Обнуление баланса пользователя {user_id}")
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute(
                "UPDATE users SET balance = 0 WHERE user_id = ?",
                (user_id,)
            )
            print(f"Баланс пользователя {user_id} обнулен")

def add_referral(user_id: int, referrer_id: int):
    """
    Регистрирует реферальную связь между пользователями.
    
    Args:
        user_id (int): ID пользователя, который был приглашен
        referrer_id (int): ID пользователя, который пригласил
    """
    print(f"Регистрация реферальной связи: пользователь {user_id} приглашен пользователем {referrer_id}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Проверяем, не был ли уже зарегистрирован этот реферал
            row = conn.execute(
                "SELECT id FROM referrals WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            
            if row is None:
                # Регистрируем новую реферальную связь
                conn.execute(
                    "INSERT INTO referrals (user_id, referrer_id) VALUES (?, ?)",
                    (user_id, referrer_id)
                )
                print(f"Зарегистрирована новая реферальная связь")
            else:
                print(f"Реферальная связь для пользователя {user_id} уже существует")

def activate_referral(user_id: int, amount: float):
    """
    Активирует реферальную связь и начисляет вознаграждение реферреру.
    Вызывается при первом пополнении баланса пользователем.
    
    Args:
        user_id (int): ID пользователя, который пополнил баланс
        amount (float): Сумма пополнения в баллах
    """
    from config import REFERRAL_REWARD_USD
    
    print(f"Активация реферальной связи для пользователя {user_id} (пополнение: {amount:.0f} баллов)")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Проверяем, есть ли реферальная связь и не была ли она уже активирована
            row = conn.execute(
                "SELECT id, referrer_id, status FROM referrals WHERE user_id = ? AND status = 'pending'",
                (user_id,)
            ).fetchone()
            
            if row is None:
                print(f"Нет ожидающей активации реферальной связи для пользователя {user_id}")
                return  # Нет реферальной связи или она уже активирована
            
            ref_id, referrer_id, status = row
            print(f"Найдена реферальная связь: ID={ref_id}, реферер={referrer_id}, статус={status}")
            
            # Используем фиксированную сумму вознаграждения из конфига
            reward = REFERRAL_REWARD_USD  # Теперь это баллы (рубли)
            print(f"Начисляем вознаграждение в размере {reward:.0f} баллов")
            
            # Обновляем статус реферальной связи
            conn.execute(
                """UPDATE referrals 
                   SET status = 'active', 
                       activated_at = CURRENT_TIMESTAMP,
                       reward_amount = ?
                   WHERE id = ?""",
                (reward, ref_id)
            )
            
            # Начисляем вознаграждение реферреру
            conn.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (reward, referrer_id)
            )
            
            # Записываем транзакцию
            conn.execute(
                """INSERT INTO transactions 
                   (user_id, amount, type, description, original_currency, original_amount) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    referrer_id,
                    reward,
                    "deposit",
                    f"Реферальное вознаграждение за пользователя {user_id}",
                    "RUB",
                    reward
                )
            )
            
            print(f"Вознаграждение успешно начислено пользователю {referrer_id}")


def get_referrals(user_id: int) -> list:
    """
    Получает список рефералов пользователя.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        list: Список словарей с информацией о рефералах
    """
    print(f"Запрос списка рефералов пользователя {user_id}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            rows = conn.execute(
                """SELECT r.id, r.user_id, r.status, r.created_at, r.activated_at, r.reward_amount,
                          u.full_name
                   FROM referrals r
                   LEFT JOIN users u ON r.user_id = u.user_id
                   WHERE r.referrer_id = ?
                   ORDER BY r.created_at DESC""",
                (user_id,)
            ).fetchall()
            
            result = [dict(row) for row in rows]
            print(f"Получено {len(result)} рефералов")
            return result
        

def get_total_referral_rewards(user_id: int) -> float:
    """
    Получает общую сумму реферальных вознаграждений пользователя.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        float: Общая сумма вознаграждений
    """
    print(f"Запрос общей суммы реферальных вознаграждений пользователя {user_id}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute(
                "SELECT SUM(reward_amount) FROM referrals WHERE referrer_id = ? AND status = 'active'",
                (user_id,)
            ).fetchone()
            
            if row and row[0]:
                total = float(row[0])
                print(f"Общая сумма вознаграждений: {total:.0f} баллов")
                return total
            
            print("Нет активных реферальных вознаграждений")
            return 0.0

# Новые функции для работы с историей сообщений

def save_message(user_id: int, sender: str, content: str, is_summary: bool = False):
    """
    Сохраняет сообщение в БД.
    
    Args:
        user_id (int): ID пользователя
        sender (str): Отправитель ('user' или 'bot')
        content (str): Содержание сообщения
        is_summary (bool): Является ли сообщение кратким содержанием
    """
    print(f"Сохранение сообщения для пользователя {user_id}: sender={sender}, is_summary={is_summary}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute(
                "INSERT INTO messages (user_id, sender, content, is_summary) VALUES (?, ?, ?, ?)",
                (user_id, sender, content, is_summary)
            )
            print(f"Сообщение сохранено в БД")

def get_last_messages(user_id: int, limit: int = 20):
    """
    Получает последние сообщения пользователя.
    
    Args:
        user_id (int): ID пользователя
        limit (int): Количество сообщений
        
    Returns:
        list: Список сообщений
    """
    print(f"Запрос последних {limit} сообщений пользователя {user_id}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            rows = conn.execute(
                """SELECT id, sender, content, is_summary, timestamp 
                   FROM messages 
                   WHERE user_id = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (user_id, limit)
            ).fetchall()
            
            result = [dict(row) for row in rows]
            result.reverse()  # Меняем порядок на хронологический (от старых к новым)
            print(f"Получено {len(result)} сообщений")
            return result

def get_message_count(user_id: int):
    """
    Подсчитывает количество сообщений пользователя.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        int: Количество сообщений
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            
            count = row[0] if row else 0
            print(f"Количество сообщений пользователя {user_id}: {count}")
            return count

def delete_old_messages(user_id: int, keep: int = 20):
    """
    Удаляет старые сообщения, оставляя указанное количество.
    
    Args:
        user_id (int): ID пользователя
        keep (int): Количество сообщений для сохранения
    """
    print(f"Удаление старых сообщений пользователя {user_id}, оставляем {keep} последних")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Получаем ID самого старого сообщения из тех, что нужно сохранить
            row = conn.execute(
                "SELECT id FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?, 1",
                (user_id, keep - 1)
            ).fetchone()
            
            if not row:
                print(f"Недостаточно сообщений для удаления ({keep - 1})")
                return  # Недостаточно сообщений
                
            threshold_id = row[0]
            
            # Удаляем сообщения старше порога
            deleted = conn.execute(
                "DELETE FROM messages WHERE user_id = ? AND id < ?",
                (user_id, threshold_id)
            ).rowcount
            
            print(f"Удалено {deleted} старых сообщений")