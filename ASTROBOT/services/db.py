"""
Сервис для работы с базой данных SQLite.
Содержит функции для инициализации БД, управления пользователями и балансом в USD.
"""

import sqlite3
from contextlib import closing
from config import SQLITE_DB_PATH
from logger import db_logger as logger

def init_db():
    """
    Инициализирует базу данных SQLite.
    Создает таблицу пользователей, если она еще не существует.
    Добавляет поле balance, если оно отсутствует.
    """
    logger.info(f"Инициализация базы данных: {SQLITE_DB_PATH}")
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
            logger.info("Таблица users создана или уже существует")
            
            # Проверяем, есть ли столбец balance, и добавляем его, если отсутствует
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'balance' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0")
                logger.info("Добавлен столбец 'balance' в таблицу 'users'")
            
            # Проверяем, есть ли столбец initial_analysis_completed, и добавляем его, если отсутствует
            if 'initial_analysis_completed' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN initial_analysis_completed BOOLEAN DEFAULT 0")
                logger.info("Добавлен столбец 'initial_analysis_completed' в таблицу 'users'")
            
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
            logger.info("Таблица transactions создана или уже существует")
            
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
            logger.info("Таблица referrals создана или уже существует")
            
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
            logger.info("Таблица messages создана или уже существует")
            
            # Создаем таблицу для приглашений совместимости
            conn.execute('''
                CREATE TABLE IF NOT EXISTS compatibility_invites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invite_code TEXT UNIQUE,
                    user_id INTEGER,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    accepted_by INTEGER,
                    accepted_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (accepted_by) REFERENCES users (user_id)
                )
            ''')
            logger.info("Таблица compatibility_invites создана или уже существует")
            
            # Проверяем наличие новых столбцов в таблице transactions
            cursor.execute("PRAGMA table_info(transactions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'original_currency' not in columns and 'id' in columns:
                conn.execute("ALTER TABLE transactions ADD COLUMN original_currency TEXT DEFAULT 'USD'")
                logger.info("Добавлен столбец 'original_currency' в таблицу 'transactions'")
                
            if 'original_amount' not in columns and 'id' in columns:
                conn.execute("ALTER TABLE transactions ADD COLUMN original_amount REAL DEFAULT 0.0")
                logger.info("Добавлен столбец 'original_amount' в таблицу 'transactions'")
                
            # Проверяем наличие столбца compatibility_type в таблице compatibility_invites
            cursor.execute("PRAGMA table_info(compatibility_invites)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'compatibility_type' not in columns and any(column == 'id' for column in columns):
                logger.info("Добавляем колонку 'compatibility_type' в таблицу 'compatibility_invites'")
                conn.execute("ALTER TABLE compatibility_invites ADD COLUMN compatibility_type TEXT DEFAULT 'general'")
                logger.info("Колонка 'compatibility_type' успешно добавлена")

def add_user_if_not_exists(user_id: int, username: str):
    """
    Добавляет пользователя в БД, если он еще не существует.
    
    Args:
        user_id (int): ID пользователя в Telegram
        username (str): Имя пользователя в Telegram
    """
    logger.debug(f"Проверяем наличие пользователя {user_id} ({username}) в БД")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row is None:
                logger.info(f"Пользователь {user_id} не найден, добавляем в БД")
                conn.execute(
                    "INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                    (user_id, username, 0.0)
                )
                logger.info(f"Пользователь {user_id} добавлен в БД")
            else:
                logger.debug(f"Пользователь {user_id} уже существует в БД")

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
    logger.info(f"Обновляем профиль пользователя {user_id}:")
    logger.debug(f"Имя: {full_name}, Дата: {birth_date}, Время: {birth_time}, Координаты: {latitude}, {longitude}, {altitude}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Сначала проверим, существует ли пользователь
            check = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if not check:
                logger.warning(f"Пользователь {user_id} не найден в БД для обновления профиля")
                # Создадим пользователя, если он не существует
                conn.execute(
                    "INSERT INTO users (user_id, username) VALUES (?, ?)",
                    (user_id, f"user_{user_id}")
                )
                logger.info(f"Пользователь {user_id} был автоматически создан")
                
            # Обновляем профиль
            conn.execute(
                """UPDATE users 
                   SET full_name = ?, birth_date = ?, birth_time = ?,
                       birth_latitude = ?, birth_longitude = ?, birth_altitude = ?
                   WHERE user_id = ?""",
                (full_name, birth_date, birth_time, latitude, longitude, altitude, user_id)
            )
            logger.info(f"Профиль пользователя {user_id} обновлен в БД")
            
            # Проверяем, что данные действительно обновились
            row = conn.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,)).fetchone()
            logger.debug(f"Проверка обновления: full_name = {row[0] if row else 'Нет данных'}")

def get_user_profile(user_id: int) -> dict:
    """
    Получает профиль пользователя из БД.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        dict: Словарь с данными пользователя или пустой словарь, если профиль не заполнен
    """
    logger.debug(f"Запрашиваем профиль для user_id={user_id}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Проверяем, существует ли пользователь
            exists_query = "SELECT 1 FROM users WHERE user_id = ?"
            user_exists = conn.execute(exists_query, (user_id,)).fetchone()
            logger.debug(f"Пользователь существует в БД: {user_exists is not None}")
            
            if not user_exists:
                logger.warning(f"Пользователь {user_id} не найден в БД")
                return {}
            
            # Получаем данные пользователя
            query = """SELECT full_name, birth_date, birth_time, birth_latitude, birth_longitude, birth_altitude, balance 
                       FROM users WHERE user_id = ?"""
            row = conn.execute(query, (user_id,)).fetchone()
            logger.debug(f"Получены данные пользователя: {row}")
            
            # Если запись существует, возвращаем словарь
            if row:
                # Проверяем основной индикатор заполненности профиля - имя
                if not row[0]:
                    logger.debug(f"Имя пользователя {user_id} не заполнено, считаем профиль пустым")
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
                logger.debug(f"Возвращаем результат: {result}")
                return result
            
            logger.debug("Строка не найдена, возвращаем пустой словарь")
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
                logger.debug(f"Баланс пользователя {user_id}: {balance:.0f} баллов")
                return balance
            logger.warning(f"Пользователь {user_id} не найден, возвращаем баланс 0.0")
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
    logger.info(f"Пополнение баланса пользователя {user_id} на {amount:.0f} баллов ({description})")
    
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
                logger.info(f"Новый баланс пользователя {user_id}: {new_balance:.0f} баллов")
                return new_balance
            logger.error(f"Пользователь {user_id} не найден после пополнения баланса")
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
    logger.info(f"Списание с баланса пользователя {user_id}: {amount:.2f} баллов ({description})")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Проверяем, достаточно ли средств
            row = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if not row:
                logger.error(f"Пользователь {user_id} не найден при попытке списания")
                return False
                
            current_balance = float(row[0]) if row[0] is not None else 0.0
            
            if current_balance < amount:
                logger.warning(f"Недостаточно средств: баланс {current_balance:.2f} баллов, требуется {amount:.2f} баллов")
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
            logger.info(f"Списание успешно. Новый баланс: {new_balance:.2f} баллов")
            
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
    logger.debug(f"Запрос истории транзакций пользователя {user_id} (лимит: {limit})")
    
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
            logger.debug(f"Получено {len(result)} транзакций")
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
    logger.debug(f"Проверка подписки пользователя {user_id}: {has_subscription} (баланс: {balance:.0f} баллов, мин. баланс: {MIN_REQUIRED_BALANCE:.0f} баллов)")
    return has_subscription

def activate_subscription(user_id: int):
    """
    Устаревший метод для обратной совместимости.
    В новой модели используйте add_to_balance.
    """
    logger.warning(f"УСТАРЕВШИЙ МЕТОД: activate_subscription вызван для пользователя {user_id}")
    # Ничего не делаем, оставляем для обратной совместимости
    pass

def deactivate_subscription(user_id: int):
    """
    Устаревший метод для обратной совместимости.
    В новой модели это обнуление баланса пользователя.
    """
    logger.info(f"Обнуление баланса пользователя {user_id}")
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute(
                "UPDATE users SET balance = 0 WHERE user_id = ?",
                (user_id,)
            )
            logger.info(f"Баланс пользователя {user_id} обнулен")

def add_referral(user_id: int, referrer_id: int):
    """
    Регистрирует реферальную связь между пользователями.
    
    Args:
        user_id (int): ID пользователя, который был приглашен
        referrer_id (int): ID пользователя, который пригласил
    """
    logger.info(f"Регистрация реферальной связи: пользователь {user_id} приглашен пользователем {referrer_id}")
    
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
                logger.info(f"Зарегистрирована новая реферальная связь")
            else:
                logger.info(f"Реферальная связь для пользователя {user_id} уже существует")

def activate_referral(user_id: int, amount: float):
    """
    Активирует реферальную связь и начисляет вознаграждение реферреру.
    Вызывается при первом пополнении баланса пользователем.
    
    Args:
        user_id (int): ID пользователя, который пополнил баланс
        amount (float): Сумма пополнения
    """
    from config import REFERRAL_REWARD_USD
    
    logger.info(f"Активация реферальной связи для пользователя {user_id} (пополнение: {amount:.0f} баллов)")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Проверяем, есть ли реферальная связь и не была ли она уже активирована
            row = conn.execute(
                "SELECT id, referrer_id, status FROM referrals WHERE user_id = ? AND status = 'pending'",
                (user_id,)
            ).fetchone()
            
            if row is None:
                logger.debug(f"Нет ожидающей активации реферальной связи для пользователя {user_id}")
                return  # Нет реферальной связи или она уже активирована
            
            ref_id, referrer_id, status = row
            logger.info(f"Найдена реферальная связь: ID={ref_id}, реферер={referrer_id}, статус={status}")
            
            # Используем фиксированную сумму вознаграждения из конфига
            reward = REFERRAL_REWARD_USD  # Теперь это баллы (рубли)
            logger.info(f"Начисляем вознаграждение в размере {reward:.0f} баллов")
            
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
            
            logger.info(f"Вознаграждение успешно начислено пользователю {referrer_id}")

def get_referrals(user_id: int) -> list:
    """
    Получает список рефералов пользователя.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        list: Список словарей с информацией о рефералах
    """
    logger.debug(f"Запрос списка рефералов пользователя {user_id}")
    
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
            logger.debug(f"Получено {len(result)} рефералов")
            return result

def get_total_referral_rewards(user_id: int) -> float:
    """
    Получает общую сумму реферальных вознаграждений пользователя.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        float: Общая сумма вознаграждений
    """
    logger.debug(f"Запрос общей суммы реферальных вознаграждений пользователя {user_id}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute(
                "SELECT SUM(reward_amount) FROM referrals WHERE referrer_id = ? AND status = 'active'",
                (user_id,)
            ).fetchone()
            
            if row and row[0]:
                total = float(row[0])
                logger.debug(f"Общая сумма вознаграждений: {total:.0f} баллов")
                return total
            
            logger.debug("Нет активных реферальных вознаграждений")
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
    logger.debug(f"Сохранение сообщения для пользователя {user_id}: sender={sender}, is_summary={is_summary}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute(
                "INSERT INTO messages (user_id, sender, content, is_summary) VALUES (?, ?, ?, ?)",
                (user_id, sender, content, is_summary)
            )
            logger.debug(f"Сообщение сохранено в БД")

def get_last_messages(user_id: int, limit: int = 20):
    """
    Получает последние сообщения пользователя.
    
    Args:
        user_id (int): ID пользователя
        limit (int): Количество сообщений
        
    Returns:
        list: Список сообщений
    """
    logger.debug(f"Запрос последних {limit} сообщений пользователя {user_id}")
    
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
            logger.debug(f"Получено {len(result)} сообщений")
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
            logger.debug(f"Количество сообщений пользователя {user_id}: {count}")
            return count

def delete_old_messages(user_id: int, keep: int = 20):
    """
    Удаляет старые сообщения, оставляя указанное количество.
    
    Args:
        user_id (int): ID пользователя
        keep (int): Количество сообщений для сохранения
    """
    logger.info(f"Удаление старых сообщений пользователя {user_id}, оставляем {keep} последних")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            # Получаем ID самого старого сообщения из тех, что нужно сохранить
            row = conn.execute(
                "SELECT id FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?, 1",
                (user_id, keep - 1)
            ).fetchone()
            
            if not row:
                logger.debug(f"Недостаточно сообщений для удаления ({keep - 1})")
                return  # Недостаточно сообщений
                
            threshold_id = row[0]
            
            # Удаляем сообщения старше порога
            deleted = conn.execute(
                "DELETE FROM messages WHERE user_id = ? AND id < ?",
                (user_id, threshold_id)
            ).rowcount
            
            logger.info(f"Удалено {deleted} старых сообщений")

def user_has_initial_analysis(user_id: int) -> bool:
    """
    Проверяет, был ли уже проведен начальный анализ Human Design для пользователя.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        bool: True, если первичный анализ уже был проведен, иначе False
    """
    logger.debug(f"Проверка наличия первичного анализа для пользователя {user_id}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute(
                "SELECT initial_analysis_completed FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            
            # Проверяем, что row существует и значение не None и не 0
            result = bool(row and row[0] == 1)
            logger.debug(f"Результат проверки для пользователя {user_id}: {result} (значение в БД: {row[0] if row else 'None'})")
            
            if result:
                logger.debug(f"Пользователь {user_id} уже проходил первичный анализ")
            else:
                logger.debug(f"Пользователь {user_id} еще не проходил первичный анализ")
            
            return result

def mark_initial_analysis_completed(user_id: int) -> None:
    """
    Отмечает, что первичный анализ Human Design был проведен для пользователя.
    
    Args:
        user_id (int): ID пользователя
    """
    logger.debug(f"Отмечаем первичный анализ как выполненный для пользователя {user_id}")
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            conn.execute(
                "UPDATE users SET initial_analysis_completed = 1 WHERE user_id = ?",
                (user_id,)
            )
            
            # Проверяем, что данные действительно обновились
            row = conn.execute(
                "SELECT initial_analysis_completed FROM users WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            
            if row and row[0]:
                logger.debug(f"Успешно: первичный анализ отмечен как выполненный для пользователя {user_id}")
            else:
                logger.error(f"Не удалось обновить статус первичного анализа для пользователя {user_id}")


# Функции для работы с проверкой совместимости

def create_compatibility_invitation(user_id: int, description: str, compatibility_type: str = "general") -> str:
    """
    Создает новое приглашение для проверки совместимости.
    
    Args:
        user_id (int): ID пользователя, создающего приглашение
        description (str): Описание приглашения (например, "для моего друга")
        compatibility_type (str): Тип совместимости: "general", "love", "friendship", "business"
        
    Returns:
        str: Сгенерированный код приглашения или None, если достигнут лимит приглашений
    """
    import uuid
    import time
    
    # Проверяем, сколько приглашений уже создал пользователь
    active_invites_count = count_user_invites(user_id)
    if active_invites_count >= 10:
        logger.warning(f"Пользователь {user_id} достиг лимита приглашений (10)")
        return None
    
    # Генерируем уникальный код приглашения
    invite_code = f"{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            try:
                conn.execute(
                    """INSERT INTO compatibility_invites 
                       (invite_code, user_id, description, compatibility_type, status) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (invite_code, user_id, description, compatibility_type, 'pending')
                )
                logger.info(f"Создано приглашение для совместимости с кодом: {invite_code}, тип: {compatibility_type}")
                return invite_code
            except Exception as e:
                logger.error(f"Ошибка при создании приглашения: {str(e)}")
                # В случае ошибки генерируем другой код
                fallback_code = f"fb_{uuid.uuid4().hex[:6]}_{int(time.time())}"
                logger.info(f"Используем запасной код: {fallback_code}")
                return fallback_code
            
def count_user_invites(user_id: int) -> int:
    """
    Подсчитывает количество активных приглашений, созданных пользователем.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        int: Количество активных приглашений
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM compatibility_invites WHERE user_id = ? AND status = 'pending'",
                (user_id,)
            ).fetchone()
            
            count = row[0] if row else 0
            logger.debug(f"Количество активных приглашений пользователя {user_id}: {count}")
            return count

def check_compatibility_invitation(invite_code: str) -> dict:
    """
    Проверяет существование и статус приглашения.
    
    Args:
        invite_code (str): Код приглашения
        
    Returns:
        dict: Информация о приглашении или None, если не найдено
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            row = conn.execute(
                "SELECT * FROM compatibility_invites WHERE invite_code = ?",
                (invite_code,)
            ).fetchone()
            
            if row:
                logger.debug(f"Найдено приглашение с кодом {invite_code}")
                return dict(row)
            
            logger.warning(f"Приглашение с кодом {invite_code} не найдено")
            return None

def accept_compatibility_invitation(invite_code: str, user_id: int) -> bool:
    """
    Отмечает приглашение как принятое.
    
    Args:
        invite_code (str): Код приглашения
        user_id (int): ID пользователя, принявшего приглашение
        
    Returns:
        bool: True, если успешно, False в случае ошибки
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        with conn:
            try:
                conn.execute(
                    """UPDATE compatibility_invites 
                       SET status = 'accepted', 
                           accepted_by = ?, 
                           accepted_at = CURRENT_TIMESTAMP
                       WHERE invite_code = ? AND status = 'pending'""",
                    (user_id, invite_code)
                )
                
                logger.info(f"Приглашение {invite_code} принято пользователем {user_id}")
                return True
            except Exception as e:
                logger.error(f"Ошибка при принятии приглашения: {str(e)}")
                return False

def get_user_compatibility_invites(user_id: int) -> list:
    """
    Получает список приглашений пользователя.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        list: Список приглашений
    """
    with closing(sqlite3.connect(SQLITE_DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            rows = conn.execute(
                """SELECT i.*, u.full_name as accepted_by_name
                   FROM compatibility_invites i
                   LEFT JOIN users u ON i.accepted_by = u.user_id
                   WHERE i.user_id = ?
                   ORDER BY i.created_at DESC""",
                (user_id,)
            ).fetchall()
            
            logger.debug(f"Получено {len(rows)} приглашений для пользователя {user_id}")
            return [dict(row) for row in rows]