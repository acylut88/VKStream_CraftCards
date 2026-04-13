import asyncio
from datetime import datetime
from database import DatabaseManager
from engine import GameEngine
import json

# Инициализируем компоненты
db = DatabaseManager()
engine = GameEngine()

# Кэш логов для отображения в браузере
game_logs = []

async def process_lootbox_opening(vk_id: str, nickname: str, is_elite: bool = False):
    user = await db.get_user(vk_id, nickname)
    
    # ✅ НОВОЕ: Проверяем ПА активацию на ПЕРВЫЙ бокс
    if user['pa_active_today'] == 0 and user['pa_charges'] > 0:
        # Это первый бокс со своим ПА - активируем
        await db.update_user_field(vk_id, "pa_charges", -1)
        await db.update_user_field(vk_id, "pa_active_today", 1)
        has_pa = True
    else:
        # Либо ПА уже активирован, либо нет зарядов
        has_pa = (user['pa_active_today'] == 1)
    
    # Считаем параметры
    box_num = (user['elite_boxes_today'] if is_elite else user['std_boxes_today']) + 1
    stars = user['stars']
    
    # 1. Считаем карты и AC
    count = engine.calculate_card_count(box_num, stars, has_pa)
    dropped_cards = engine.get_random_cards(box_num, has_pa, count, is_elite)
    ac_reward = engine.calculate_ac_reward(box_num, is_elite, has_pa)
    
    # 2. Пишем в базу
    await db.add_raw_cards(vk_id, dropped_cards)
    await db.update_ac(vk_id, ac_reward)
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
    
    # ✅ НОВОЕ: Отслеживание событий (гонка на 10 уровень, AC фарм, редкие карты)
    session = await db.get_current_active_session()
    if session and session['status'] == 'active':
        # Получить текущий инвентарь игрока
        inventories = await db.get_all_inventories_grouped()
        player_inventory = inventories.get(vk_id, [])
        
        # Проверяем, достиг ли кто-то 10 уровня
        for inv in player_inventory:
            if inv['card_level'] == 10:
                # Заканчиваем сессию - нашли победителя!
                await db.finish_stream_session(session['session_id'])
                
                # Сохраняем результат
                await db.update_user_event_progress(
                    session['session_id'],
                    vk_id,
                    'card',
                    10,
                    cards_data=json.dumps(player_inventory)
                )
                break
        
        # Обновляем AC лидерборд
        current_ac = (await db.get_user(vk_id))['ac_today']
        await db.update_user_event_progress(
            session['session_id'],
            vk_id,
            'ac_farming',
            current_ac
        )
        
        # Записываем редкие дропы (вероятность >= 0.25%)
        for card in dropped_cards:
            # Получить вероятность из weights
            weights_table = None
            if is_elite:
                weights_table = engine.elite_box_weights[str(min(box_num, 3))]
            elif has_pa:
                weights_table = engine.pa_box_weights[str(min(box_num, 12))]
            else:
                weights_table = engine.standard_weights[str(min(box_num, 12))]
            
            probability = weights_table[card['lvl'] - 1] / 100.0
            
            if probability >= 0.0025:  # 0.25%
                await db.record_rare_drop(
                    session['session_id'],
                    vk_id,
                    nickname,
                    card['type'],
                    card['lvl'],
                    probability,
                    'Элитный' if is_elite else 'Стандарт'
                )
    
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