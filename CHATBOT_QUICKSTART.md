# 🚀 QUICK START - ChatBot для CraftCards

## ✅ Статус проекта

Все файлы чат-бота успешно созданы и протестированы!

```
chatbot/
├── bot/
│   ├── bot_Main.py      ✅ Playwright мониторинг чата
│   ├── bot_Handler.py   ✅ Обработка команд (!карты, !топ, !стат, etc.)
│   └── bot_Users.py     ✅ Управление пользователями
├── constants/
│   ├── cnst_Bot.py      ✅ Команды и тексты
│   ├── cnst_VK.py       ✅ Настройки VK API
│   └── cnst_Server.py   ✅ Серверные настройки
├── database/
│   └── database.py      ✅ Отдельная БД чат-бота
├── services/
│   └── craftcards_api.py ✅ Клиент к CraftCards API
├── utils/
│   └── bot_utils.py     ✅ Отправка/удаление сообщений
├── README.md            ✅ Документация
└── requirements.txt     ✅ Зависимости
```

## 🎯 Что дальше? (План действий)

### 1. НАСТРОЙКА (5 минут)

**Изменить `chatbot/constants/cnst_VK.py`:**
```python
CHANNEL_NAME = "ваш_канал_vk"
CHAT_PAGE_URL = "https://vkvideo.ru/ваша_страница_чата"
HEADERS = {"Authorization": "Bearer YOUR_TOKEN"}
```

**Изменить `chatbot/constants/cnst_Server.py`:**
```python
CHROME_PROFILE_PATH = "C:/путь/к/профилю/Chrome"
```

### 2. УСТАНОВКА ЗАВИСИМОСТЕЙ (2 минуты)

```bash
cd chatbot
pip install -r requirements.txt
playwright install chromium
```

### 3. ИНИЦИАЛИЗАЦИЯ БД (1 минута)

```bash
python -c "import asyncio; from chatbot.database.database import init_db; asyncio.run(init_db())"
```

### 4. ЗАПУСК (1 минута)

**ОДИН ТЕРМИНАЛ - ВСЁ ВКЛЮЧЕНО!**

```bash
python api.py
```

Чат-бот стартует автоматически в фоне! 🎉

При запуске ты увидишь:
```
[Startup] Starting VKStream CraftCards API...
[ChatBot] Initializing background task...
[ChatBot] Database initialized
[ChatBot] Background task started
```

## 🎮 Доступные команды чат-бота

| Команда | Описание |
|---------|----------|
| `!карты` | Инвентарь пользователя |
| `!топ` | Лидерборд (карты + AC) |
| `!стат` | Личная статистика |
| `!инфо` | Правила игры |
| `!регистрация` | Регистрация нового пользователя |
| `!боксы` | Информация о шансах |

## 📊 Архитектура интеграции

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

## 🔧 Возможные ошибки

### Ошибка: "Chrome не найден"
```bash
playwright install chromium
```

### Ошибка: "API не отвечает"
- Убедитесь что CraftCards API запущен на порту 8001
- Проверьте `http://127.0.0.1:8001/api/analytics` в браузере

### Ошибка: "Авторизация VK"
- При первом запуске бот откроет Chrome
- У вас 60 секунд чтобы войти в VK

## 📝 Следующие шаги (Фаза 2)

После успешного запуска можно добавить:
- [ ] Квесты за игровые действия
- [ ] Рейды через чат (массовые открытия боксов)
- [ ] Турниры между зрителями
- [ ] Автоматические розыгрыши
- [ ] Интеграция со StreamLive

---

**Готово! 🎉** Чат-бот интегрирован как микросервис и готов к запуску.
