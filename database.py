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
                    elite_boxes_today INTEGER DEFAULT 0
                )
            ''')
            # Таблица инвентаря
            await db.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id TEXT,
                    card_type TEXT,
                    card_level INTEGER,
                    quantity INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, card_type, card_level),
                    FOREIGN KEY (user_id) REFERENCES users(vk_id)
                )
            ''')
            await db.commit()

    async def get_user(self, vk_id, nickname=None):
        """Получает юзера или создает нового (Welcome-бонус: 3 звезды + 2 ПА)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE vk_id = ?", (vk_id,)) as cursor:
                user = await cursor.fetchone()
                
            if not user and nickname:
                await db.execute("""
                    INSERT INTO users (vk_id, nickname, stars, pa_charges) 
                    VALUES (?, ?, 3, 2)
                """, (vk_id, nickname))
                await db.commit()
                return await self.get_user(vk_id)
            return user

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
        """Красная кнопка: сброс дня и понижение звезд"""
        async with aiosqlite.connect(self.db_path) as db:
            # Понижаем звезды прогульщикам
            await db.execute("UPDATE users SET stars = MAX(1, stars - 1) WHERE std_boxes_today < 12")
            # Обнуляем счетчики
            await db.execute("UPDATE users SET std_boxes_today = 0, elite_boxes_today = 0, pa_active_today = 0")
            await db.commit()

    async def get_all_users_admin(self):
        """Для вывода списка в админке FastAPI"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users") as cursor:
                return await cursor.fetchall()
