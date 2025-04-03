"""
Конфигурационный файл с настройками бота.
Содержит токены, ключи API, пути к файлам и URL для API запросов.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
SQLITE_DB_PATH = os.path.join(BASE_DIR, "database.db")  # Путь к файлу базы данных
PDF_FILE_PATH = "book1.pdf"     # Путь к PDF-файлу с экспертной информацией

# Пути к файлам для формирования личности рефлектора у бота
KEY1_DOCX_PATH = os.path.join(BASE_DIR, "datasets", "key1.docx")
KEY2_DOCX_PATH = os.path.join(BASE_DIR, "datasets", "key2.docx")

# Настройки CrystalPay API
CRYSTALPAY_SECRET_KEY = "efec7f0c4fcf79d95c64005fd702aee542c890c7"
CRYSTALPAY_SALT = "0f59e52269077cdea009bebc9d686f5d3ff8ca3a"
CRYSTALPAY_API_URL = "https://api.crystalpay.io/v3"  # Обновлено до v3
CRYSTALPAY_CASHIER_URL = "https://crystalpay.io/invoice"  # Обновлен формат URL
CRYSTALPAY_WALLET_ID = "astrobotv1"  # ID кассы

# Настройки оплаты в рублях (баллах)
MIN_REQUIRED_BALANCE = 100  # Минимальный баланс для общения с ботом (в баллах)

# Настройки системы оплаты токенов
# Базовая цена за 1 токен в рублях (баллах)
# $150 за 1 млн токенов Output = 0.015 рубля за токен при курсе $1 = 100 руб
TOKEN_PRICE = 0.015  # Цена за 1 токен вывода в рублях (баллах)

# Коэффициенты для различных типов запросов
# Input = $75 за 1 млн токенов, что в 2 раза дешевле Output
INPUT_TOKEN_MULTIPLIER = 0.5  # Множитель для входящих токенов (в 2 раза дешевле, чем исходящие)
OUTPUT_TOKEN_MULTIPLIER = 1.0  # Множитель для исходящих токенов (полная стоимость)

# Токены для анализа Human Design
HD_ANALYSIS_TOKENS = 6667  # Эквивалент токенов для анализа Human Design (~100 баллов)

# Настройки бота
BOT_USERNAME = "cz_astrobot_bot"  # Username вашего бота без символа @

# Настройки реферальной системы
REFERRAL_REWARD_USD = 300  # Вознаграждение 300 баллов за каждого приведенного пользователя

# Настройки Yandex SpeechKit
YANDEX_SPEECHKIT_FOLDER_ID = "b1gv3g9g2aplg7cuvthf"  # ID каталога
YANDEX_SPEECHKIT_API_KEY = "AQVNyJrzHeGpK4VFG2Nl4bHbR0paVBwZvJdZD9XZ"  # Новый API-ключ
YANDEX_SPEECHKIT_API_KEY_ID = "aje8jbphrod95e2ka6r3"  # ID API-ключа

# Настройки голоса и параметров синтеза
YANDEX_SPEECHKIT_VOICE = "filipp"  # Мужской голос (вместо alena)
YANDEX_SPEECHKIT_EMOTION = "neutral"  # Доступные эмоции: neutral, good, evil
YANDEX_SPEECHKIT_SPEED = 0.9  # Немного замедляем для более спокойного темпа (было 1.0)

# Стоимость конвертации в аудио (в баллах)
AUDIO_CONVERSION_COST = 20

# Ограничения для аудио-сообщений
MAX_AUDIO_TEXT_LENGTH = 10000  # Максимальная длина текста для конвертации в аудио

# API ключ для доступа к данным базы через REST API
API_SECRET_KEY = "yNkP8Qz2XbTr5Vw7JsLm3GfHd9AeC6B1"  # Замените на сгенерированный надежный ключ