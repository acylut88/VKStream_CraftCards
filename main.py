import asyncio
from datetime import datetime
from database import DatabaseManager
from engine import GameEngine

# Инициализируем основные компоненты
db = DatabaseManager()
engine = GameEngine()

# Глобальный кэш логов для быстрого отображения в FastAPI
game_logs = []

async def process_lootbox_opening(vk_id: str, nickname: str, is_elite: bool = False):
    """
    Основной оркестратор: обрабатывает команду открытия бокса, 
    считает дроп, делает мерж и пишет логи.
    """
    
    # 1. Получаем данные пользователя из БД
    user = await db.get_user(vk_id, nickname)
    
    # 2. Определяем параметры для расчета
    # Если бокс элитный, берем его счетчик (1-3), иначе стандартный (1-12)
    box_num = (user['elite_boxes_today'] if is_elite else user['std_boxes_today']) + 1
    has_pa = user['pa_charges'] > 0
    stars = user['stars']
    
    # 3. Рассчитываем количество карт через Engine
    count = engine.calculate_card_count(box_num, stars, has_pa)
    
    # 4. Генерируем случайные карты
    dropped_cards = engine.get_random_cards(box_num, has_pa, count, is_elite)
    
    # 5. Сохраняем выпавшие карты ("сырой дроп") в БД
    await db.add_raw_cards(vk_id, dropped_cards)
    
    # 6. Обновляем счетчики боксов и списываем ПА (если это первый бокс за стрим)
    await db.increment_box_counter(vk_id, is_elite)
    
    # 7. Запускаем автоматический мерж (2-в-1) в БД
    merges = await db.perform_auto_merge(vk_id)
    
    # --- ЛОГИРОВАНИЕ ---
    
    # Формируем списки редких карт и успешных мержей для лога
    # Считаем редким всё, что 4 уровня и выше
    rare_list = [f"{c['type']}-{c['lvl']}" for c in dropped_cards if c['lvl'] >= 4]
    merge_list = [f"{m['type']}-{m['to_lvl']}" for m in merges if m['to_lvl'] >= 5]
    
    # Сохраняем лог в постоянную таблицу БД
    await db.add_log(
        nickname=nickname,
        box_type="Элитный" if is_elite else "Стандарт",
        count=count,
        rare_drops=rare_list,
        merges=merge_list,
        is_elite=is_elite
    )
    
    # Обновляем оперативный кэш логов для админки
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "nickname": nickname,
        "box_type": "Элитный" if is_elite else "Стандарт",
        "count": count,
        "rare_drops": ", ".join(rare_list),
        "merges": ", ".join(merge_list)
    }
    game_logs.insert(0, log_entry)
    if len(game_logs) > 100:
        game_logs.pop()
        
    # Проверка на победу (карта 10 уровня)
    has_win = any(m['to_lvl'] == 10 for m in merges)
    
    return {
        "status": "success",
        "nickname": nickname,
        "dropped_count": count,
        "is_winner": has_win,
        "rare_count": len(rare_list)
    }

async def finish_stream_logic():
    """
    Логика 'Красной кнопки': экспорт весов в CSV и сброс игрового дня.
    """
    # 1. Сбор весов всех игроков
    weights_data = await db.get_all_weights()
    
    # 2. Экспорт в CSV через Engine (разделитель '|')
    engine.export_to_csv(weights_data, filename="players_weight.csv")
    
    # 3. Сброс счетчиков, расчет лояльности (звезд) в БД
    await db.reset_day()
    
    return True

# --- Инициализация при старте (вызывается из web_admin.py) ---
async def init_app():
    await db.init_db()
    # Подгружаем последние 100 логов из базы в кэш при запуске
    recent_logs = await db.get_recent_logs(100)
    game_logs.clear()
    game_logs.extend(recent_logs)
