# --- Настройки Сервера ---
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CraftCards API
CRAFTCARDS_API_URL = "http://127.0.0.1:8001"
CRAFTCARDS_API_TIMEOUT = 5

# Настройки бота
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8002  # Отдельный порт для чат-бота (если нужен свой API)

# Путь к профилю Chrome для Playwright
CHROME_PROFILE_PATH = os.path.join(BASE_DIR, "chatbot_chrome_profile")

# Создаем директорию если не существует
os.makedirs(CHROME_PROFILE_PATH, exist_ok=True)

# Таймауты и интервалы
BOT_PAGE_LOAD_WAIT = 5
BOT_POLL_INTERVAL = 0.3
BOT_ERROR_WAIT = 5
BOT_CACHE_LIMIT = 5000
BOT_CACHE_CLEANUP = 2000

# Debounce (защита от спама)
DEBOUNCE_SECONDS = 3
DEBOUNCE_CACHE_LIMIT = 100
DEBOUNCE_CLEANUP_MULTIPLIER = 2

# HTTP
HTTP_TIMEOUT = 5
HTTP_STATUS_OK = 200

# Логирование
LOG_LEVEL = "INFO"
LOG_TO_FILE = False
LOG_FILE_PATH = os.path.join(BASE_DIR, "chatbot.log")
