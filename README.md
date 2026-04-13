# 🎮 VKStream CraftCards - React Admin Panel

**Полнофункциональная админ-панель для управления игровой системой VKStream.**

> Разработано с React 18 + TypeScript + FastAPI

![Status](https://img.shields.io/badge/status-ready-brightgreen) ![License](https://img.shields.io/badge/license-MIT-blue)

---

## 🎯 Что это?

Современная админ-панель для управления игровой системой VKStream с такими функциями:

- 📊 **Dashboard** - Аналитика и статистика
- 👥 **Управление игроками** - CRUD операции  
- 🎁 **BoxManager** - Выдача боксов N рарности для игроков
- 📜 **Логирование** - История всех события в real-time
- ⚡ **Real-time обновления** - WebSocket интеграция

---

## ⚡ Быстрый старт (5 минут)

### 1️⃣ Запуск API (Terminal 1)

```bash
cd VKStream_CraftCards
python api.py
```

✅ API на http://localhost:8001

### 2️⃣ Запуск Фронтенда (Terminal 2)

```bash
cd VKStream_CraftCards/frontend
npm install
npm run dev
```

✅ Админка на http://localhost:5173

### 3️⃣ Готово!

Откройте браузер → **http://localhost:5173** и начните управлять игрой! 🚀

---

## 🎨 UI/UX Features

### Dashboard 📊
```
┌─────────────────────────────────────┐
│  Всего игроков  │  Активных        │
│      24         │      18           │
├─────────────────────────────────────┤
│  Всего боксов   │  Всего AC        │
│     1,240       │    12,450        │
├─────────────────────────────────────┤
│  Распределение боксов  │  ТОП 10    │
│  [Диаграмма]          │  [Таблица] │
└─────────────────────────────────────┘
```

### PlayerManagement 👥
```
┌─────────────────────────────────────┐
│ [Поиск по нику/ID]                 │
├─────────────────────────────────────┤
│ Ник      │ ⭐ │ ⚡ │ Боксы │ AC   │
├──────────┼────┼───┼──────┼──────┤
│ Player1  │ 3  │ 2 │ 12/3 │ 250  │
│ Player2  │ 2  │ 0 │  0/0 │  50  │
│ ...      │... │..│ ...  │ ...  │
└─────────────────────────────────────┘
```

### BoxManager 🎁 ⭐⭐⭐
```
┌──────────────────────────────────────┐
│ ВЫДАТЬ БОКСЫ                         │
├──────────────────────────────────────┤
│ Пользователь:  [Player123        ]  │
│ Тип:           [○ Стандартный    ]  │
│                [● Элитный       ]  │
│ Рарность:      [Уровень 2       ]  │
│ Количество:    [5              ]  │
│                                      │
│  ┌──────────────────────────────┐  │
│  │   📦 Выдать боксы           │  │
│  └──────────────────────────────┘  │
│                                      │
│ Превью: 5x Элитный (уровень 2)    │
│ Карты: 1-2 уровня                 │
└──────────────────────────────────────┘
```

---

## 📚 API Документация

### Все эндпоинты

| Метод | Endpoint | Описание |
|-------|----------|---------|
| GET | `/api/users` | Список всех игроков |
| GET | `/api/users/{vk_id}` | Данные игрока |
| POST | `/api/users/{vk_id}/update` | Обновить параметры |
| POST | `/api/users/{vk_id}/boxes` | **Выдать боксы** |
| DELETE | `/api/users/{vk_id}` | Удалить игрока |
| GET | `/api/analytics` | Dashboard данные |
| GET | `/api/logs` | Логи событий |
| POST | `/api/stream/finish` | Завершить стрим |

### Выдача боксов (POST /api/users/{vk_id}/boxes)

```json
{
  "vk_id": "user123",
  "nickname": "Player",
  "count": 5,
  "rarity": 2
}
```

**Параметры:**
- `count` - количество боксов (1-100)
- `rarity` - рарность элитного бокса (1/2/3) или 0 для стандартного

**Ответ:**
```json
{
  "status": "success",
  "boxes_added": 5,
  "results": [
    {
      "timestamp": "14:30:25",
      "nickname": "Player",
      "box_type": "Элитный (рарность 2)",
      "count": 8,
      "rare_drops": "ST-4, TT-5",
      "merges": "LT-3",
      "ac_won": 40
    },
    ...
  ]
}
```

---

## 🛠️ Технологии

### Backend
| Технология | Версия | Назначение |
|-----------|--------|-----------|
| Python | 3.10+ | Язык |
| FastAPI | 0.135.3 | REST API |
| SQLite | - | База данных |
| Pydantic | 2.12.5 | Валидация |
| aiosqlite | 0.22.1 | Асинхронная БД |

### Frontend
| Технология | Версия | Назначение |
|-----------|--------|-----------|
| React | 18.2.0 | UI |
| TypeScript | 5.3 | Type safety |
| Vite | 5.0 | Build tool |
| Tailwind | 3.3 | CSS |
| Recharts | 2.10 | Графики |
| Zustand | 4.4 | State |
| Axios | 1.6 | HTTP |

---

## 📂 Структура папок

```
VKStream_CraftCards/
│
├── api.py                    ✨ Запускается на :8001
├── main.py                   
├── engine.py                 
├── database.py               
│
├── frontend/                 ✨ React приложение
│   ├── src/
│   │   ├── components/       Все компоненты UI
│   │   ├── services/         API клиент
│   │   ├── store/            State management
│   │   └── App.tsx           
│   ├── package.json          npm зависимости
│   ├── vite.config.ts        
│   └── README.md             
│
├── SETUP_GUIDE.md            Полное руководство
└── requirements.txt          Python зависимости
```

---

## 🎮 Примеры использования BoxManager

### Пример 1: Новичок получает первый бокс
```
1. Выберите игрока "NewPlayer"
2. Тип: Стандартный
3. Количество: 1
4. Нажмите "Выдать боксы" ✓
```

### Пример 2: Поощрение активного игрока
```
1. Выберите "TopPlayer"
2. Тип: Элитный
3. Рарность: 3 (максимум)
4. Количество: 5
5. Он получит редкие карты! 🔥
```

### Пример 3: Тестирование баланса
```
1. Выберите "TestUser"
2. Тип: Стандартный
3. Количество: 20
4. Смотрите как растет статистика на Dashboard
```

---

## 🔐 Безопасность

⚠️ **Текущее состояние:**
- ✅ CORS разрешен (локально)
- ✅ Валидация данных через Pydantic
- ⚠️ **TODO:** Аутентификация администраторов
- ⚠️ **TODO:** Rate limiting

---

## 🚀 Production Deploy

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Docker Compose

```yaml
version: '3'
services:
  api:
    build: .
    ports:
      - "8001:8001"
    volumes:
      - ./stream_game.db:/app/stream_game.db
  
  frontend:
    image: node:18
    working_dir: /app
    command: npm run build && npm install -g serve && serve -s dist
    ports:
      - "5173:3000"
    volumes:
      - ./frontend:/app
```

---

## 🐛 Troubleshooting

### "Cannot GET /api/users"
```bash
# Проверьте что api.py запущен
python api.py

# Попробуйте явно:
curl http://localhost:8001/api/users
```

### "npm modules not found"
```bash
cd frontend
npm install
npm run dev
```

### "Proxy error in frontend"
```bash
# Убедитесь что api.py на порту 8001
# И фронтенд на 5173

# В браузере откройте DevTools (F12)
# Network → проверьте запросы к /api
```

---

## 📊 Архитектура системы

```
┌─────────────────────────────────████████┐
│   📱 React Frontend (Vite)      ████████│
│   http://localhost:5173          ████████│
│                                  ████████│
│   • Dashboard (Recharts)        ████████│
│   • Player Management           ████████│
│   • BoxManager ⭐              ████████│
│   • Logs (Real-time)            ████████│
└──────────────┬────────────────────────┘
               │ HTTP + WebSocket 🔗
               ▼
┌─────────────────────────────────████████┐
│   ⚙️  FastAPI Backend           ████████│
│   http://localhost:8001          ████████│
│                                  ████████│
│   • REST API                    ████████│
│   • WebSocket Live              ████████│
│   • Business Logic              ████████│
│   • Data Validation             ████████│
└──────────────┬────────────────────────┘
               │ Async SQL 🔗
               ▼
┌─────────────────────────────────████████┐
│   📦 SQLite Database            ████████│
│   stream_game.db                 ████████│
│                                  ████████│
│   • users table                 ████████│
│   • inventory table             ████████│
│   • logs table                  ████████│
└─────────────────────────────────████████┘
```

---

## 📝 Лицензия

MIT License © 2026 VKStream Team

---

## 📞 Помощь

Возникли вопросы? Смотрите:
1. [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Полное руководство
2. [frontend/README.md](./frontend/README.md) - Документация фронтенда
3. Terminal logs для ошибок

---

**Версия:** 1.0.0  
**Статус:** ✅ Production Ready  
**Последнее обновление:** 2026-04-13  

**Создано с ❤️ для VKStream**
