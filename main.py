import asyncio
from database import DatabaseManager
from engine import GameEngine

db = DatabaseManager()
engine = GameEngine()

async def process_lootbox_opening(vk_id, nickname, is_elite=False):
    """Логика обработки открытия бокса"""
    # 1. Получаем юзера (или создаем новичка)
    user = await db.get_user(vk_id, nickname)
    
    # 2. Определяем номер бокса для выбора весов
    box_num = (user['elite_boxes_today'] if is_elite else user['std_boxes_today']) + 1
    has_pa = user['pa_charges'] > 0
    
    # 3. Считаем кол-во и генерируем дроп
    count = engine.calculate_card_count(box_num, user['stars'], has_pa)
    dropped_cards = engine.get_random_cards(box_num, has_pa, count, is_elite)
    
    # 4. Сохраняем "сырой" дроп
    await db.add_raw_cards(vk_id, dropped_cards)
    
    # 5. Обновляем счетчики боксов и ПА
    await db.increment_box_counter(vk_id, is_elite)
    
    # 6. Запускаем мерж
    merges = await db.perform_auto_merge(vk_id)
    
    # Проверяем редкие события (для уведомлений)
    rare_drops = [c for c in dropped_cards if c['lvl'] >= 5] # Пример
    has_win = any(m['to_lvl'] == 10 for m in merges)
    
    return {
        "nickname": nickname,
        "dropped_count": count,
        "merges_count": len(merges),
        "rare_drops": rare_drops,
        "is_winner": has_win
    }

async def finish_stream_logic():
    """Финальная 'Красная кнопка'"""
    # Выгружаем веса
    weights_data = await db.get_all_weights()
    engine.export_to_csv(weights_data)
    
    # Сбрасываем день и понижаем звезды
    await db.reset_day()
    return "CSV сохранен, база обновлена."

# Для тестов (можно запустить просто main.py)
if __name__ == "__main__":
    async def test():
        await db.init_db()
        res = await process_lootbox_opening("test_id", "Gamer123")
        print(f"Результат теста: {res}")
    
    asyncio.run(test())
