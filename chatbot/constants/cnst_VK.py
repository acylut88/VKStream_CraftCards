# --- Настройки VK API ---

# Название канала VK Video
CHANNEL_NAME = "scr"

# URL страницы чата
CHAT_PAGE_URL = f"https://live.vkvideo.ru/{CHANNEL_NAME}/stream/default/only-chat"

# Заголовки для VK API (если нужен прямой доступ к API)
HEADERS = {
    "Authorization": "Bearer 0a8ac7a1ea0bc78b889cafe9e0260c5cc6bc6396396cfdd373208738ae5013ac",
    "Content-Type": "application/json"
}

# Время ожидания загрузки страницы (секунды)
PAGE_LOAD_TIMEOUT = 60000

# Время авторизации (если не залогинен)
AUTH_WAIT_SECONDS = 60

# --- VK Live API для трекинга зрителей ---
VK_LIVE_API_TOKEN = "0a8ac7a1ea0bc78b889cafe9e0260c5cc6bc6396396cfdd373208738ae5013ac"
VK_LIVE_CHANNEL_NAME = "scr"
