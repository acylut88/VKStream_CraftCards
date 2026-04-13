# 🎮 VKStream CraftCards - Project Context

## 📋 О проекте
**VKStream CraftCards** - интерактивная игровая система для стримов VK Video Live с админ-панелью на React.

**Ключевая механика:**
- Зрители получают лутбоксы с картами (ЛТ, СТ, ТТ, ПТ) 10 уровней
- Авто-мерж 2-в-1 (две одинаковые карты → одна уровнем выше)
- Прогрессивная сложность (шансы на редкий дроп растут с каждым боксом)
- Финальный розыгрыш на основе веса коллекции: Weight = 2^(Level-1)

## 🏗️ Архитектура

### Backend (Python)
- **FastAPI** 0.135.3 на порту 8001
- **aiosqlite** для асинхронной работы с SQLite
- **Pydantic** 2.12.5 для валидации данных

### Frontend (React)
- **React 18.2** + **TypeScript 5.3**
- **Vite 5.0** на порту 5173
- **Tailwind CSS** + **Recharts** + **Zustand** + **Axios**

## 📁 Структура ключевых файлов

```
VKStream_CraftCards/
├── api.py                    # REST API + WebSocket (порт 8001)
├── main.py                   # Бизнес-логика, process_lootbox_opening
├── engine.py                 # GameEngine: расчеты карт, веса, CSV экспорт
├── database.py               # DatabaseManager: все SQL операции
├── web_admin.py              # Старая админка (порт 8000) - legacy
└── frontend/                 # React приложение
```

## 🎯 Игровая механика

### Типы боксов:
1. **Standard** (боксы 1-12) - базовые шансы, прогрессивно улучшаются
2. **PA (Premium)** (боксы 1-12) - x1.75 карт, лучше шансы, активируется за заряды
3. **Elite** (рарность 1-3) - элитные боксы с гарантированными уровнями

### Ключевые формулы:
- **Количество карт:** base = 4 + box_num * 2 (PA: x1.75, 3 звезды: x1.5, 2 звезды: +3)
- **AC奖励:** standard: box_num*2, elite: box_num*10, PA: x2
- **Вес карты:** 2^(Level-1)

### Система лояльности:
- Welcome-бонус: 3 звезды + ПА на 2 стрима
- Retention: понижение звезд за пропуск стримов
- PA заряды: первый бокс со своим ПА активирует его

## 🔑 API Endpoints

```
GET  /api/users                      # Список пользователей
GET  /api/users/{vk_id}              # Данные конкретного
POST /api/users                      # Создать пользователя
POST /api/users/{vk_id}/update       # Обновить параметры
DELETE /api/users/{vk_id}            # Удалить
POST /api/users/{vk_id}/boxes        # Выдать боксы
GET  /api/users/{vk_id}/inventory    # Инвентарь

GET  /api/analytics                  # Dashboard данные
GET  /api/logs                       # История событий
GET  /api/stats/timeline             # Временная шкала

POST /api/stream/finish              # Завершить стрим
POST /api/stream/start-day           # Сброс PA для всех
POST /api/stream/session/create      # Создать сессию
POST /api/stream/session/{id}/finish # Завершить сессию

GET  /api/stream/leaderboard/{id}/{type}  # Лидерборд
GET  /api/stream/overlay/*           # OBS overlays

WS   /ws/live                        # Real-time обновления
```

## 🧪 Тестирование (в процессе)
- Unit-тесты для engine.py
- Unit-тесты для database.py  
- Integration-тесты для api.py
- Запуск: `pytest`

## 🚀 Запуск проекта

### Terminal 1 - Backend:
```bash
cd VKStream_CraftCards
python api.py
```

### Terminal 2 - Frontend:
```bash
cd frontend
npm install
npm run dev
```

## ⚠️ TODO (приоритеты)
- [ ] Добавить аутентификацию администраторов (JWT)
- [ ] Rate limiting
- [ ] Логирование ошибок через logging модуль
- [ ] CI/CD с автотестами
- [ ] Docker Compose для деплоя
- [ ] Переход на PostgreSQL для production

## 📝 Заметки
- Версия: 1.0-MVP
- Статус: Production Ready (для MVP)
- Последнее обновление: 2026-04-13
- Оценка проекта: 8/10
