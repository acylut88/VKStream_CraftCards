import aiosqlite
import asyncio

class DatabaseManager:
    def __init__(self, db_path="stream_game.db"):
        self.db_path = db_path

    async def init_db(self):
        """Создание таблиц при запуске (вызывать в основном стартапе)"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    vk_id TEXT PRIMARY KEY,
                    nickname TEXT,
                    stars INTEGER DEFAULT 3,
                    pa_charges INTEGER DEFAULT 0,
                    pa_active_today INTEGER DEFAULT 0,
                    std_boxes_today INTEGER DEFAULT 0,
                    elite_boxes_today INTEGER DEFAULT 0,
                    ac_balance INTEGER DEFAULT 0,
                    ac_today INTEGER DEFAULT 0
                )
            ''')
            # Таблица инвентаря
            await db.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id TEXT, card_type TEXT, card_level INTEGER, quantity INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, card_type, card_level)
                )
            ''')
            await db.commit()
            await db.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    nickname TEXT,
                    box_type TEXT,
                    count INTEGER,
                    rare_drops TEXT,
                    merges TEXT,
                    is_elite INTEGER DEFAULT 0,
                    ac_won INTEGER DEFAULT 0
                )
            ''')
            
            # Таблица потоков (стримерские сессии)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS stream_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stream_date DATE,
                    stream_name TEXT,
                    event_type TEXT,
                    status TEXT DEFAULT 'active',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    notes TEXT
                )
            ''')
            
            # Таблица результатов событий
            await db.execute('''
                CREATE TABLE IF NOT EXISTS stream_event_results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    event_type TEXT,
                    player_vk_id TEXT NOT NULL,
                    player_nickname TEXT,
                    rank INTEGER,
                    value INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    json_data TEXT,
                    FOREIGN KEY (session_id) REFERENCES stream_sessions(session_id)
                )
            ''')
            
            # Таблица снимков состояния (real-time tracking)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS stream_session_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    vk_id TEXT NOT NULL,
                    event_type TEXT,
                    current_rank INTEGER,
                    current_value INTEGER,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    card_distribution TEXT,
                    ac_earned_this_stream INTEGER DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES stream_sessions(session_id)
                )
            ''')
            
            # Таблица редких дропов
            await db.execute('''
                CREATE TABLE IF NOT EXISTS stream_rare_drops (
                    drop_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    vk_id TEXT NOT NULL,
                    nickname TEXT,
                    card_type TEXT,
                    card_level INTEGER,
                    probability REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    box_type TEXT,
                    FOREIGN KEY (session_id) REFERENCES stream_sessions(session_id)
                )
            ''')
            
            await db.commit()

    async def get_user(self, vk_id, nickname=None):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE vk_id = ?", (vk_id,)) as cursor:
                user = await cursor.fetchone()
            if not user and nickname:
                await db.execute("INSERT INTO users (vk_id, nickname, stars, pa_charges) VALUES (?, ?, 3, 2)", (vk_id, nickname))
                await db.commit()
                return await self.get_user(vk_id)
            return user
    
    async def update_ac(self, vk_id, amount):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET ac_balance = MAX(0, ac_balance + ?), 
                ac_today = MAX(0, ac_today + ?) WHERE vk_id = ?
            """, (amount, amount, vk_id))
            await db.commit()

    async def add_raw_cards(self, vk_id, cards):
        """Добавляет выпавшие из бокса карты в инвентарь (без мержа)"""
        async with aiosqlite.connect(self.db_path) as db:
            for card in cards:
                await db.execute("""
                    INSERT INTO inventory (user_id, card_type, card_level, quantity)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(user_id, card_type, card_level) 
                    DO UPDATE SET quantity = quantity + 1
                """, (vk_id, card['type'], card['lvl']))
            await db.commit()

    async def increment_box_counter(self, vk_id, is_elite=False):
        """Считает боксы и списывает ПА если нужно"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT pa_charges, pa_active_today FROM users WHERE vk_id = ?", (vk_id,)) as cursor:
                user = await cursor.fetchone()
            
            if user['pa_charges'] > 0 and user['pa_active_today'] == 0:
                await db.execute("""
                    UPDATE users SET pa_charges = pa_charges - 1, pa_active_today = 1 
                    WHERE vk_id = ?
                """, (vk_id,))

            field = "elite_boxes_today" if is_elite else "std_boxes_today"
            await db.execute(f"UPDATE users SET {field} = {field} + 1 WHERE vk_id = ?", (vk_id,))
            await db.commit()

    async def perform_auto_merge(self, vk_id):
        """Логика '2-в-1' внутри базы. Возвращает список успешных слияний."""
        merge_events = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            for card_type in ['LT', 'ST', 'TT', 'PT']:
                for lvl in range(1, 10):
                    async with db.execute("""
                        SELECT quantity FROM inventory 
                        WHERE user_id = ? AND card_type = ? AND card_level = ?
                    """, (vk_id, card_type, lvl)) as cursor:
                        row = await cursor.fetchone()
                    
                    if not row or row['quantity'] < 2:
                        continue
                    
                    count = row['quantity']
                    new_cards = count // 2
                    remainder = count % 2
                    
                    await db.execute("""
                        UPDATE inventory SET quantity = ? 
                        WHERE user_id = ? AND card_type = ? AND card_level = ?
                    """, (remainder, vk_id, card_type, lvl))
                    
                    await db.execute("""
                        INSERT INTO inventory (user_id, card_type, card_level, quantity)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(user_id, card_type, card_level) 
                        DO UPDATE SET quantity = quantity + ?
                    """, (vk_id, card_type, lvl + 1, new_cards, new_cards))
                    
                    merge_events.append({"type": card_type, "to_lvl": lvl + 1, "count": new_cards})
            await db.commit()
        return merge_events

    async def get_all_weights(self):
        """Сбор данных для CSV"""
        export_data = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT vk_id, nickname FROM users") as cursor:
                users = await cursor.fetchall()
            
            for user in users:
                async with db.execute("SELECT card_level, quantity FROM inventory WHERE user_id = ?", (user['vk_id'],)) as cursor:
                    inv = await cursor.fetchall()
                
                weight = sum((2**(item['card_level'] - 1)) * item['quantity'] for item in inv)
                if weight > 0:
                    export_data.append({"nickname": user['nickname'], "weight": weight})
        return export_data

    async def reset_day(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET stars = MAX(1, stars - 1) WHERE std_boxes_today < 12")
            await db.execute("UPDATE users SET std_boxes_today = 0, elite_boxes_today = 0, pa_active_today = 0, ac_today = 0")
            await db.commit()

    async def get_all_users_admin(self):
        """Для вывода списка в админке FastAPI"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users") as cursor:
                return await cursor.fetchall()

    async def get_all_inventories_grouped(self):
        """Возвращает словари инвентарей для всех юзеров: {vk_id: [cards]}"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Сортируем по уровню, чтобы редкие карты были в начале списка
            async with db.execute("SELECT * FROM inventory WHERE quantity > 0 ORDER BY card_level DESC") as cursor:
                rows = await cursor.fetchall()
                data = {}
                for r in rows:
                    if r['user_id'] not in data:
                        data[r['user_id']] = []
                    data[r['user_id']].append(dict(r))
                return data

    async def update_user_field(self, vk_id, field, change=None, action=None):
        """Update user field with support for increment/reset operations"""
        allowed = ["stars", "pa_charges", "ac_balance", "pa_active_today"]
        if field not in allowed: 
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            if action == "reset":
                # Reset field to 0
                await db.execute(f"UPDATE users SET {field} = 0 WHERE vk_id = ?", (vk_id,))
            elif isinstance(change, int):
                # Increment field (change can be positive or negative)
                await db.execute(f"UPDATE users SET {field} = MAX(0, {field} + ?) WHERE vk_id = ?", (change, vk_id))
            await db.commit()

    async def add_log(self, nickname, box_type, count, rare_drops, merges, is_elite, ac_won=0):
        """Добавляет запись в лог событий (включая AC)"""
        async with aiosqlite.connect(self.db_path) as db:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Превращаем списки в строки для хранения в БД
            rare_str = ", ".join(rare_drops) if rare_drops else ""
            merges_str = ", ".join(merges) if merges else ""

            await db.execute("""
                INSERT INTO logs (timestamp, nickname, box_type, count, rare_drops, merges, is_elite, ac_won)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, nickname, box_type, count, rare_str, merges_str, 1 if is_elite else 0, ac_won))
            await db.commit()

    async def clear_all_inventories(self):
        """Полная очистка всех карт у всех игроков"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM inventory")
            await db.commit()

    async def clear_user_inventory(self, vk_id):
        """Удаление всех карт конкретного пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM inventory WHERE user_id = ?", (vk_id,))
            await db.commit()
            
    async def get_recent_logs(self, limit=100):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
            
    async def clear_full_database(self):
        """Полная очистка: удаление ВСЕХ юзеров и ВСЕХ инвентарей"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM inventory")
            await db.execute("DELETE FROM users")
            await db.commit()

    async def delete_user_completely(self, vk_id):
        """Полное удаление пользователя и его вещей из базы"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM inventory WHERE user_id = ?", (vk_id,))
            await db.execute("DELETE FROM users WHERE vk_id = ?", (vk_id,))
            await db.commit()

    async def create_user(self, vk_id, nickname, stars=3, pa_charges=0):
        """Создать нового пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Проверяем, существует ли пользователь
            async with db.execute("SELECT * FROM users WHERE vk_id = ?", (vk_id,)) as cursor:
                existing = await cursor.fetchone()
            if existing:
                raise ValueError(f"User with vk_id {vk_id} already exists")
            
            await db.execute(
                "INSERT INTO users (vk_id, nickname, stars, pa_charges) VALUES (?, ?, ?, ?)",
                (vk_id, nickname, stars, pa_charges)
            )
            await db.commit()
            return await self.get_user(vk_id)

    async def rename_user(self, vk_id, new_nickname):
        """Смена никнейма зрителя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET nickname = ? WHERE vk_id = ?", (new_nickname, vk_id))
            await db.commit()

    # ========== STREAM EVENTS METHODS ==========
    
    async def create_stream_session(self, event_type, stream_date, stream_name=None):
        """Создать новую потоковую сессию"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO stream_sessions (stream_date, stream_name, event_type, status)
                VALUES (?, ?, ?, 'active')
            """, (stream_date, stream_name, event_type))
            await db.commit()
            
            async with db.execute("SELECT session_id FROM stream_sessions ORDER BY session_id DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def get_current_active_session(self):
        """Получить текущую активную сессию"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM stream_sessions 
                WHERE status = 'active' 
                ORDER BY created_at DESC LIMIT 1
            """) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def finish_stream_session(self, session_id):
        """Завершить потоковую сессию"""
        async with aiosqlite.connect(self.db_path) as db:
            from datetime import datetime
            await db.execute("""
                UPDATE stream_sessions 
                SET status = 'completed', completed_at = ? 
                WHERE session_id = ?
            """, (datetime.now().isoformat(), session_id))
            await db.commit()

    async def update_user_event_progress(self, session_id, vk_id, event_type, value, cards_data=None):
        """Обновить прогресс игрока в событии"""
        import json
        async with aiosqlite.connect(self.db_path) as db:
            json_data = json.dumps(cards_data) if cards_data else None
            
            # Проверяем, есть ли уже запись
            async with db.execute("""
                SELECT snapshot_id FROM stream_session_snapshots
                WHERE session_id = ? AND vk_id = ? AND event_type = ?
            """, (session_id, vk_id, event_type)) as cursor:
                existing = await cursor.fetchone()
            
            if existing:
                # Обновляем существующую запись
                await db.execute("""
                    UPDATE stream_session_snapshots
                    SET current_value = ?, card_distribution = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE session_id = ? AND vk_id = ? AND event_type = ?
                """, (value, json_data, session_id, vk_id, event_type))
            else:
                # Создаем новую запись
                await db.execute("""
                    INSERT INTO stream_session_snapshots 
                    (session_id, vk_id, event_type, current_value, card_distribution)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, vk_id, event_type, value, json_data))
            
            await db.commit()

    async def get_current_leaderboard(self, session_id, event_type, limit=10):
        """Получить текущий лидерборд для события"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM stream_session_snapshots
                WHERE session_id = ? AND event_type = ?
                ORDER BY current_value DESC
                LIMIT ?
            """, (session_id, event_type, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_ac_leaderboard(self, session_id, limit=10):
        """Получить лидерборд по AC за сессию"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT vk_id, 
                       (SELECT nickname FROM users WHERE vk_id = stream_session_snapshots.vk_id) as nickname,
                       ac_earned_this_stream,
                       ROW_NUMBER() OVER (ORDER BY ac_earned_this_stream DESC) as rank
                FROM stream_session_snapshots
                WHERE session_id = ? AND event_type = 'ac_farming'
                ORDER BY ac_earned_this_stream DESC
                LIMIT ?
            """, (session_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def record_rare_drop(self, session_id, vk_id, nickname, card_type, level, probability, box_type):
        """Записать редкий дроп"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO stream_rare_drops 
                (session_id, vk_id, nickname, card_type, card_level, probability, box_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, vk_id, nickname, card_type, level, probability, box_type))
            await db.commit()

    async def get_recent_rare_drops(self, session_id, limit=5):
        """Получить последние редкие дропы"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM stream_rare_drops
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def reset_pa_active_today_all(self):
        """Сбросить pa_active_today для ВСЕх игроков"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET pa_active_today = 0")
            await db.commit()

    async def get_session_results(self, session_id: int, event_type: str):
        """Получить финальные результаты сессии (для CSV export)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT vk_id, 'vk_id' as vk_id, current_value, ac_earned_this_stream
                FROM stream_session_snapshots
                WHERE session_id = ? AND event_type = ?
                ORDER BY current_value DESC
            """, (session_id, event_type)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_session_info(self, session_id: int):
        """Получить информацию о сессии"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT session_id, stream_date, stream_name, event_type, status, created_at, completed_at
                FROM stream_sessions
                WHERE session_id = ?
            """, (session_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_stream_sessions_all(self):
        """Получить все сессии (для архива)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT session_id, stream_date, stream_name, event_type, status, created_at, completed_at
                FROM stream_sessions
                ORDER BY created_at DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    
