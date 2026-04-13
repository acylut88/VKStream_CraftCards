# VKStream Admin Panel (React + TypeScript)

Современная админ-панель для управления игровой системой VKStream CraftCards.

## 🚀 Быстрый старт

### Требования
- Node.js 16+ 
- npm или yarn

### Установка

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Панель доступна по адресу: `http://localhost:5173`

**⚠️ Убедитесь, что бэкенд API запущен на `http://localhost:8001`**

### Build для production

```bash
npm run build
```

## 📋 Функции

### Dashboard
- 📊 Общая статистика (количество игроков, боксов, AC)
- 📈 Аналитика и графики
- 🏆 Топ-10 лучших игроков
- 📉 Распределение боксов

### Управление игроками
- 👥 Список всех игроков
- ✏️ Редактирование параметров (звёзды, ПА, AC)
- 🔍 Поиск по нику или ID
- 🗑️ Удаление пользователей

### Выдача боксов
- 🎁 Начисление N боксов пользователю
- 📦 Поддержка стандартных и элитных боксов
- 🔮 Выбор рарности для элитных боксов (1, 2, 3 уровень)
- 📋 Превью результатов

### Логирование
- 📜 История всех событий (открытия боксов)
- 🔥 Отслеживание редких карт
- 🛠️ Логирование мержей
- ⏰ Real-time обновления

## 🏗️ Архитектура

```
frontend/
├── src/
│   ├── components/          # React компоненты
│   │   ├── Dashboard.tsx    # Главная страница
│   │   ├── PlayerManagement.tsx
│   │   ├── BoxManager.tsx   # ⭐ Выдача боксов
│   │   └── Logs.tsx
│   ├── services/
│   │   └── api.ts           # API клиент (axios)
│   ├── store/
│   │   └── index.ts         # State management (zustand)
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

## 🔌 API Эндпоинты

- `GET /api/users` - Список пользователей
- `GET /api/users/{vk_id}` - Данные пользователя
- `POST /api/users/{vk_id}/update` - Обновить пользователя
- `POST /api/users/{vk_id}/boxes` - Начислить боксы
- `GET /api/analytics` - Аналитика
- `GET /api/logs` - Логи
- `POST /api/stream/finish` - Завершить стрим
- `WS /ws/live` - Real-time обновления

## 📦 Зависимости

- **React 18** - UI фреймворк
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Стилизация
- **Recharts** - Графики
- **Zustand** - State management
- **Axios** - HTTP клиент
- **Lucide React** - Иконки

## 🎨 UI/UX

- 🌙 Современный дизайн
- 📱 Адаптивный layout (мобильные, планшеты, ПК)
- ⚡ Real-time обновления через WebSocket
- 🎯 Интуитивная навигация

## 🔒 Безопасность

⚠️ **TODO**: Добавить аутентификацию и авторизацию

## 📝 Лицензия

Проект VKStream CraftCards

---

**Разработал:** VKStream Team  
**Версия:** 1.0  
**Дата:** 2026
