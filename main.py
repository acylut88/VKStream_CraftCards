import asyncio
from datetime import datetime
from database import DatabaseManager
from engine import GameEngine

# Инициализируем компоненты
db = DatabaseManager()
engine = GameEngine()

# Кэш логов для отображения в браузере
game_logs = []

async def process_lootbox_opening(vk_id: str, nickname: str, is_elite: bool = False):
    user = await db.get_user(vk_id, nickname)
    
    # Считаем параметры
    box_num = (user['elite_boxes_today'] if is_elite else user['std_boxes_today']) + 1
    has_pa = user['pa_charges'] > 0
    stars = user['stars']
    
    # 1. Считаем карты и AC
    count = engine.calculate_card_count(box_num, stars, has_pa)
    # ИСПРАВЛЕНО: передаем правильные параметры
    dropped_cards = engine.get_random_cards(box_num, has_pa, count, is_elite)
    ac_reward = engine.calculate_ac_reward(box_num, is_elite, has_pa)
    
    # 2. Пишем в базу
    await db.add_raw_cards(vk_id, dropped_cards)
    await db.update_ac(vk_id, ac_reward) # Начисляет и в общий, и в дневной
    await db.increment_box_counter(vk_id, is_elite)
    
    # 3. Мерж
    merges = await db.perform_auto_merge(vk_id)
    
    # 4. Логирование
    rare_list = [f"{c['type']}-{c['lvl']}" for c in dropped_cards if c['lvl'] >= 4]
    merge_list = [f"{m['type']}-{m['to_lvl']}" for m in merges if m['to_lvl'] >= 5]
    
    await db.add_log(
        nickname=nickname,
        box_type="Элитный" if is_elite else "Стандарт",
        count=count,
        rare_drops=rare_list,
        merges=merge_list,
        is_elite=is_elite,
        ac_won=ac_reward
    )
    
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "nickname": nickname,
        "box_type": "Элитный" if is_elite else "Стандарт",
        "count": count,
        "rare_drops": ", ".join(rare_list),
        "merges": ", ".join(merge_list),
        "ac_won": ac_reward
    }
    game_logs.insert(0, log_entry)
    if len(game_logs) > 100: game_logs.pop()
    
    return log_entry

async def export_raffle(mode: str):
    """
    ФУНКЦИЯ ЭКСПОРТА (теперь она точно есть!)
    mode: 'AC' - экспорт билетов за стрим, 'WEIGHT' - экспорт по весу карт
    """
    data_for_export = []
    
    if mode == "AC":
        # Тянем из базы ac_today (билеты за текущий стрим)
        async with db._get_connection() as conn: # или используй метод в database.py
            conn.row_factory = db.Row # если используешь aiosqlite
            async with conn.execute("SELECT nickname, ac_today as weight FROM users WHERE ac_today > 0") as cursor:
                rows = await cursor.fetchall()
                data_for_export = [dict(r) for r in rows]
    else:
        # Считаем веса карт (2^(L-1))
        # Можно вызвать метод из database, который мы писали ранее
        data_for_export = await db.get_all_weights()
    
    filename = f"raffle_{mode}.csv"
    engine.export_csv(data_for_export, filename)
    return filename

async def finish_stream_logic():
    """Сброс дня"""
    await db.reset_day()
    return True