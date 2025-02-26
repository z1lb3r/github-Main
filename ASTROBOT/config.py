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