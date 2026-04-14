# 🤖 ChatBot для VKStream CraftCards

Чат-бот для взаимодействия со зрителями VK Video через команды в чате.

## 📋 Возможности

- ✅ **Мониторинг чата VK** - чтение сообщений через Playwright
- ✅ **Команды для CraftCards** - `!карты`, `!топ`, `!стат`, `!инфо`, `!регистрация`, `!боксы`
- ✅ **Интеграция с API** - общение с CraftCards API (порт 8001)
- ✅ **Регистрация пользователей** - авто-регистрация новых зрителей
- ✅ **Debounce** - защита от спама
- ✅ **Авто-удаление сообщений** - бот удаляет свои сообщения после ответа

## 🚀 Установка

### 1. Установить зависимости

```bash
cd chatbot
pip install -r requirements.txt
playwright install chromium
```

### 2. Настроить константы

Отредактируйте файл `chatbot/constants/cnst_VK.py`:

```python
# Название канала VK Video
CHANNEL_NAME = "your_channel_name"

# URL страницы чата
CHAT_PAGE_URL = "https://vkvideo.ru/chat"

# Токен VK API (если нужен)
HEADERS = {
    "Authorization": "Bearer YOUR_TOKEN_HERE"
}
```

Отредактируйте `chatbot/constants/cnst_Server.py`:

```python
# CraftCards API (должен быть запущен)
CRAFTCARDS_API_URL = "http://127.0.0.1:8001"

# Путь к профилю Chrome
CHROME_PROFILE_PATH = "путь/к/вашему/профилю"
```

### 3. Инициализировать базу данных

```python
import asyncio
from chatbot.database.database import init_db

async def setup():
    await init_db()

asyncio.run(setup())
```

## 💻 Запуск

### ⭐ Вариант 1: Через api.py (РЕКОМЕНДУЕТСЯ)

Чат-бот запускается **вместе с CraftCards API** - один терминал!

```bash
# Просто запусти api.py - чат-бот стартует автоматически в фоне!
python api.py
```

При запуске ты увидишь:
```
[Startup] Starting VKStream CraftCards API...
[ChatBot] Initializing background task...
[ChatBot] Database initialized
[ChatBot] Background task started
```

### Вариант 2: Прямой запуск (для отладки)

```bash
cd chatbot
python bot/bot_Main.py
```

### Вариант 2: Интеграция с FastAPI

```python
from fastapi import FastAPI
from chatbot.bot.bot_Main import bot_task

app = FastAPI()

@app.on_event("startup")
async def startup():
    asyncio.create_task(bot_task())
```

### Вариант 3: Отдельный процесс

```bash
# Terminal 1 - CraftCards API
python api.py

# Terminal 2 - ChatBot
python chatbot/bot/bot_Main.py
```

## 🎮 Команды бота

| Команда | Описание |
|---------|----------|
| `!карты`, `!к` | Показать инвентарь карт |
| `!топ`, `!рейтинг` | Текущий лидерборд |
| `!стат`, `!стата` | Личная статистика (AC, боксы, звезды) |
| `!инфо`, `!правила` | Правила игры CraftCards |
| `!регистрация`, `!рег` | Зарегистрироваться в игре |
| `!боксы`, `!шансы` | Информация о боксах и шансах |

## 📁 Структура

```
chatbot/
├── bot/
│   ├── bot_Main.py      # Главный цикл (Playwright)
│   ├── bot_Handler.py   # Обработка команд
│   └── bot_Users.py     # Управление пользователями
├── constants/
│   ├── cnst_Bot.py      # Команды и тексты
│   ├── cnst_VK.py       # Настройки VK
│   └── cnst_Server.py   # Серверные настройки
├── database/
│   └── database.py      # БД чат-бота (отдельная)
├── services/
│   └── craftcards_api.py # Клиент к API CraftCards
├── utils/
│   └── bot_utils.py     # Утилиты (отправка/удаление сообщений)
└── requirements.txt
```

## ⚙️ Настройка

### Добавить новые команды

В `bot_Handler.py`:

```python
# В функции handle_command
elif lower_text.startswith('!мояКоманда'):
    await cmd_my_command(sender_name, msg_id)

# Новая функция
async def cmd_my_command(nick: str, msg_id: str):
    msg = "Ответ бота"
    msg_id_response = await send_private_message(nick, msg)
    if msg_id_response:
        await delete_message_via_api(msg_id_response)
```

### Изменить тексты сообщений

В `constants/cnst_Bot.py` измените тексты приветствий и правил.

## 🔧 Важно

- **Chrome Profile**: Бот использует существующий профиль Chrome для авторизации в VK
- **Debounce**: Защита от дублирования (3 секунды по умолчанию)
- **Auto-delete**: Бот удаляет свои сообщения после отправки
- **API Dependency**: Требуется запущенный CraftCards API на порту 8001

## 🐛 Отладка

Включите логирование в `cnst_Server.py`:

```python
LOG_LEVEL = "DEBUG"
LOG_TO_FILE = True
```

## 📊 Архитектура

```
┌─────────────┐
│ VK Video    │
│ Chat        │
└─────┬───────┘
      │ Playwright
      ↓
┌──────────────────────────────┐
│  api.py (FastAPI :8001)     │
│  ├── CraftCards API         │
│  └── ChatBot (background)   │  ← Встроено!
└─────┬────────────────────────┘
      │
      ↓
┌──────────────────────────────┐
│  Databases                   │
│  ├── craftcards.db (SQLite) │
│  └── chatbot.db (SQLite)    │
└──────────────────────────────┘
```

Чат-бот работает как **фоновая задача внутри api.py** - один терминал для всего!

## 📝 Лицензия

Внутренний проект VKStream CraftCards.
