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

# Настройки подписки
SUBSCRIPTION_PRICE = 5.00  # Цена подписки в рублях
SUBSCRIPTION_CURRENCY = "RUB"  # Валюта для оплаты
SUBSCRIPTION_DURATION_DAYS = 30  # Продолжительность подписки в днях

# Настройки бота
BOT_USERNAME = "cz_astrobot"  # Username вашего бота без символа @