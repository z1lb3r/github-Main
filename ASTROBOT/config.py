"""
Конфигурационный файл с настройками бота.
Содержит токены, ключи API, пути к файлам и URL для API запросов.
"""

# Настройки Telegram бота
CONFIG_TELEGRAM_BOT_TOKEN = "7859921634:AAFdMXnXr1v8uwCrkWZuWrz1cgJ6QRg9UFU"

# Настройки OpenAI API
OPENAI_API_KEY = "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"

# URL для запросов к geo.holos.house
HOLOS_COMPOSITE_URL = "https://geo.holos.house/api/composite"
HOLOS_DREAM_URL = "https://geo.holos.house/api/body-mini"  # Альтернативный URL: "https://geo.holos.house/api/dream"

# Ключ API для geo.holos.house
HOLOS_API_KEY = "CsUWmPDlHHqvqae23FxhANqkKiDVIdxd"

# Пути к файлам
SQLITE_DB_PATH = "database.db"  # Путь к файлу базы данных
PDF_FILE_PATH = "book1.pdf"     # Путь к PDF-файлу с экспертной информацией

# Пути к файлам для формирования личности рефлектора у бота
KEY1_DOCX_PATH = "datasets/key1.docx"
KEY2_DOCX_PATH = "datasets/key2.docx"

# Настройки CrystalPay API
CRYSTALPAY_SECRET_KEY = "efec7f0c4fcf79d95c64005fd702aee542c890c7"
CRYSTALPAY_SALT = "0f59e52269077cdea009bebc9d686f5d3ff8ca3a"
CRYSTALPAY_API_URL = "https://api.crystalpay.io/v3"  # Обновлено до v3
CRYSTALPAY_CASHIER_URL = "https://crystalpay.io/invoice"  # Обновлен формат URL
CRYSTALPAY_WALLET_ID = "astrobotv1"  # ID кассы

# Настройки оплаты
DEPOSIT_AMOUNT_RUB = 500  # Стандартная сумма пополнения в рублях
DEPOSIT_AMOUNT_USD = 5.00  # Эквивалент в долларах США
DISPLAY_CURRENCY = "USD"  # Валюта для отображения баланса пользователю

# Настройки системы оплаты токенов
# $15 за 1 миллион токенов = $0.000015 за 1 токен
TOKEN_PRICE = 0.000015  # Цена за 1 токен в долларах США
MIN_REQUIRED_BALANCE = 0.1  # Минимальный баланс для общения с ботом (в долларах)

# Коэффициенты для различных типов запросов
INPUT_TOKEN_MULTIPLIER = 0.5  # Множитель для входящих токенов (дешевле, чем исходящие)
OUTPUT_TOKEN_MULTIPLIER = 1.0  # Множитель для исходящих токенов (полная стоимость)
HD_ANALYSIS_TOKENS = 6667  # Эквивалент токенов для анализа Human Design (~$0.1)

# Настройки бота
BOT_USERNAME = "cz_astrobot_bot"  # Username вашего бота без символа @

# Настройки реферальной системы
REFERRAL_REWARD_USD = 3.00  # Вознаграждение $3 за каждого приведенного пользователя