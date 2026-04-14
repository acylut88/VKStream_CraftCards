"""
Обработчик сообщений и команд для CraftCards
"""
import asyncio
import re
from typing import Optional
from chatbot.constants import (
    IGNORED_USERS, BOT_COMMANDS, BOT_TRIGGERS,
    RULES_MESSAGE, BOXES_INFO_MESSAGE,
    ACCOUNT_NOT_LINKED_MESSAGE
)
from chatbot.utils.bot_utils import send_private_message, delete_message_via_api
from chatbot.database.database import get_db, get_db_cm
from chatbot.bot.bot_Users import ensure_user_exists
from chatbot.services.craftcards_api import craftcards_api


async def handle_reward_notification(text_content: str, msg_id: str):
    """
    Обработать сообщение от ChatBot о выдаче награды.
    
    Формат: "SkilloCrabs получает награду: LootBox - Standart за 1"
    Формат: "ChatBot: SkilloCrabs получает награду: LootBox - ELITE за 1"
    """
    try:
        # Парсим паттерн: {nickname} получает награду: {reward_name} за {count}
        pattern = r'(.+?)\s+получает награду:\s+(.+?)\s+за\s+(\d+)'
        match = re.search(pattern, text_content)
        
        if not match:
            return  # Не награда - игнорируем
        
        nickname = match.group(1).strip()
        reward_name = match.group(2).strip()
        count = int(match.group(3))
        
        # Убираем префикс "ChatBot:" если есть
        if nickname.startswith('ChatBot:'):
            nickname = nickname.replace('ChatBot:', '').strip()
        if nickname.startswith('ChatBot '):
            nickname = nickname.replace('ChatBot ', '').strip()
        
        print(f"[Reward] {nickname} получает {reward_name} x{count}")
        
        # Проверяем тип награды
        if 'LootBox - Standart' in reward_name:
            box_type = 'standard'
        elif 'LootBox - ELITE' in reward_name:
            box_type = 'elite'
        else:
            print(f"[Reward] Unknown reward type: {reward_name}")
            return  # Неизвестный тип награды - игнорируем
        
        # === РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ (если не зарегистрирован) ===
        user = await craftcards_api.get_user(nickname)
        
        if not user:
            print(f"[Reward] User {nickname} not registered. Auto-registering...")
            # Автоматически регистрируем пользователя
            success = await craftcards_api.create_user(
                vk_id=nickname,
                nickname=nickname,
                stars=3,  # Welcome-бонус
                pa_charges=0
            )
            
            if success:
                print(f"[Reward] {nickname} auto-registered successfully")
            else:
                print(f"[Reward] Failed to auto-register {nickname}")
                return
        
        # === ОТКРЫВАЕМ БОКСЫ ===
        await open_boxes_for_user(nickname, count, box_type)
        
    except Exception as e:
        print(f"[Reward] Error handling reward: {e}")


async def open_boxes_for_user(nickname: str, count: int, box_type: str):
    """
    Открыть боксы для пользователя через API.
    
    count = количество активаций награды.
    Каждая активация = 1 вызов API (API сам считает box_num из БД).
    """
    try:
        import httpx
        from chatbot.constants.cnst_Server import CRAFTCARDS_API_URL, HTTP_TIMEOUT

        # Определяем rarity для API
        rarity = 0 if box_type == 'standard' else 1  # 0 = standard, 1 = elite

        # Для каждой активации вызываем API отдельно
        for activation in range(1, count + 1):
            print(f"[Reward] Opening box {activation}/{count} for {nickname}")
            
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(
                    f"{CRAFTCARDS_API_URL}/api/users/{nickname}/boxes",
                    json={
                        "vk_id": nickname,
                        "nickname": nickname,
                        "count": 1,  # ВАЖНО: 1 активация = 1 вызов
                        "rarity": rarity
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Логируем результаты
                    results = result.get('results', [])
                    for res in results:
                        card_count = res.get('count', 0)
                        rare_drops = res.get('rare_drops', '')
                        merges = res.get('merges', '')
                        ac_won = res.get('ac_won', 0)
                        
                        print(f"[Reward] Activation {activation}: {card_count} cards")
                        if rare_drops:
                            print(f"[Reward]   Rare drops: {rare_drops}")
                        if merges:
                            print(f"[Reward]   Merges: {merges}")
                        print(f"[Reward]   AC: +{ac_won}")
                else:
                    print(f"[Reward] Failed to open box. Status: {response.status_code}")
        
        print(f"[Reward] Opened {count} activation(s) for {nickname}")
                
    except Exception as e:
        print(f"[Reward] Error opening boxes: {e}")


async def process_message(msg_data):
    """
    Обработать сообщение из чата
    msg_data: dict с 'id', 'text', 'sender', 'recipient' (optional)
    """
    try:
        mid = msg_data.get('id')
        text_content = (msg_data.get('text') or '').strip()
        sender_name = (msg_data.get('sender') or '').strip().replace(':', '')
        recipient = (msg_data.get('recipient') or '').strip().replace(':', '')
        lower_text = text_content.lower()

        if not mid or not sender_name:
            return

        # Игнорировать системных пользователей
        if sender_name in IGNORED_USERS:
            return

        # === ПРОВЕРКА СООБЩЕНИЙ ОТ CHATBOT О НАГРАДАХ ===
        if sender_name == 'ChatBot':
            await handle_reward_notification(text_content, mid)
            return

        # Убедиться что пользователь существует
        uid = await ensure_user_exists(sender_name, skip_greeting=True)
        svk_id = str(uid) if uid else sender_name

        # Обработать команды
        if text_content.startswith('!'):
            await handle_command(sender_name, lower_text, mid)
            return

    except Exception as e:
        print(f"[Handler] Error processing message: {e}")


async def handle_command(sender_name: str, lower_text: str, msg_id: str):
    """Обработать команды бота"""
    
    # --- !карты / !инвентарь ---
    if any(lower_text.startswith(cmd) for cmd in BOT_COMMANDS["CARDS"]):
        await cmd_cards(sender_name, msg_id)
    
    # --- !топ / !рейтинг ---
    elif any(lower_text.startswith(cmd) for cmd in BOT_COMMANDS["TOP"]):
        await cmd_top(sender_name, msg_id)
    
    # --- !стат / !статистика ---
    elif any(lower_text.startswith(cmd) for cmd in BOT_COMMANDS["STATS"]):
        await cmd_stats(sender_name, msg_id)
    
    # --- !help / !инфо ---
    elif any(lower_text.startswith(cmd) for cmd in BOT_COMMANDS["HELP"]):
        await cmd_help(sender_name, msg_id)
    
    # --- !регистрация ---
    elif any(lower_text.startswith(cmd) for cmd in BOT_COMMANDS["REGISTER"]):
        await cmd_register(sender_name, msg_id)
    
    # --- !боксы / !шансы ---
    elif any(lower_text.startswith(cmd) for cmd in BOT_COMMANDS["BOXES"]):
        await cmd_boxes(sender_name, msg_id)
    
    # --- !открыть / !бокс ---
    elif any(lower_text.startswith(cmd) for cmd in BOT_COMMANDS["OPEN"]):
        await cmd_open_box(sender_name, msg_id)
    
    # --- !новыйстрим / !сброс ---
    elif any(lower_text.startswith(cmd) for cmd in BOT_COMMANDS["NEW_STREAM"]):
        await cmd_new_stream(sender_name, msg_id)
    
    # --- !время / !сессия ---
    elif any(lower_text.startswith(cmd) for cmd in BOT_COMMANDS["VIEWER_TIME"]):
        await cmd_viewer_time(sender_name, msg_id)
    
    # --- !бонусы ---
    elif any(lower_text.startswith(cmd) for cmd in BOT_COMMANDS["VIEWER_BONUSES"]):
        await cmd_viewer_bonuses(sender_name, msg_id)


async def cmd_cards(nick: str, msg_id: str):
    """Показать инвентарь пользователя"""
    try:
        inventory = await craftcards_api.get_user_inventory(nick)
        
        if not inventory:
            msg = ACCOUNT_NOT_LINKED_MESSAGE
            msg_id_response = await send_private_message(nick, msg)
            if msg_id_response:
                await delete_message_via_api(msg_id_response)
            return
        
        cards = inventory.get('cards', [])
        if not cards:
            msg = "📦 У тебя пока нет карт. Открой боксы чтобы начать коллекцию!"
        else:
            # Группировать карты по типу и уровню
            card_summary = {}
            for card in cards:
                key = f"{card['card_type']}-{card['card_level']}"
                card_summary[key] = card_summary.get(key, 0) + 1
            
            # Форматировать вывод
            lines = ["🎮 Твоя коллекция карт:"]
            for card_key, count in sorted(card_summary.items()):
                lines.append(f"  • {card_key}: {count} шт.")
            
            msg = "\n".join(lines)
        
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)
    except Exception as e:
        print(f"[Handler] Error in !cards: {e}")


async def cmd_top(nick: str, msg_id: str):
    """Показать лидерборд"""
    try:
        # Получить активную сессию
        session = await craftcards_api.get_active_session()
        
        if not session:
            msg = "📊 Нет активной сессии. Лидерборд недоступен."
        else:
            session_id = session['session_id']
            
            # Получить карточный лидерборд
            card_lb = await craftcards_api.get_leaderboard(session_id, 'card', limit=5)
            
            # Получить AC лидерборд
            ac_lb = await craftcards_api.get_ac_leaderboard(session_id, limit=5)
            
            lines = ["🏆 ТОП StreamCraftCards:"]
            
            if card_lb:
                lines.append("\n🃏 ТОП Карты:")
                for idx, entry in enumerate(card_lb[:5], 1):
                    lines.append(f"  {idx}. {entry.get('nickname', 'N/A')}: {entry.get('current_value', 0)} уровень")
            
            if ac_lb:
                lines.append("\n💰 ТОП AC:")
                for idx, entry in enumerate(ac_lb[:5], 1):
                    lines.append(f"  {idx}. {entry.get('nickname', 'N/A')}: {entry.get('current_value', 0)} AC")
            
            msg = "\n".join(lines)
        
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)
    except Exception as e:
        print(f"[Handler] Error in !top: {e}")


async def cmd_stats(nick: str, msg_id: str):
    """Показать статистику пользователя"""
    try:
        user = await craftcards_api.get_user(nick)
        
        if not user:
            msg = ACCOUNT_NOT_LINKED_MESSAGE
            msg_id_response = await send_private_message(nick, msg)
            if msg_id_response:
                await delete_message_via_api(msg_id_response)
            return
        
        # Форматировать статистику
        lines = [
            f"📊 Твоя статистика CraftCards:",
            f"",
            f"⭐ Звезды: {user.get('stars', 0)}",
            f"🔋 PA заряды: {user.get('pa_charges', 0)}",
            f"💎 AC баланс: {user.get('ac_balance', 0)}",
            f"📦 Стандартных боксов сегодня: {user.get('std_boxes_today', 0)}",
            f"🎁 Элитных боксов сегодня: {user.get('elite_boxes_today', 0)}",
            f"💰 AC сегодня: {user.get('ac_today', 0)}",
        ]
        
        msg = "\n".join(lines)
        
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)
    except Exception as e:
        print(f"[Handler] Error in !stats: {e}")


async def cmd_help(nick: str, msg_id: str):
    """Показать правила игры"""
    msg_id_response = await send_private_message(nick, RULES_MESSAGE)
    if msg_id_response:
        await delete_message_via_api(msg_id_response)


async def cmd_register(nick: str, msg_id: str):
    """Зарегистрировать пользователя"""
    try:
        user = await craftcards_api.get_user(nick)
        
        if user:
            msg = f"✅ Ты уже зарегистрирован в CraftCards! Напиши !карты чтобы увидеть инвентарь."
        else:
            # Создать пользователя
            success = await craftcards_api.create_user(
                vk_id=nick,
                nickname=nick,
                stars=3,  # Welcome-бонус
                pa_charges=0
            )
            
            if success:
                msg = (
                    f"🎉 Добро пожаловать в CraftCards, {nick}!\n"
                    f"Ты получил 3 звезды в качестве бонуса.\n"
                    f"Напиши !инфо чтобы узнать правила."
                )
            else:
                msg = "⚠️ Ошибка регистрации. Попробуй позже или обратись к стримеру."
        
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)
    except Exception as e:
        print(f"[Handler] Error in !register: {e}")


async def cmd_boxes(nick: str, msg_id: str):
    """Показать информацию о боксах"""
    msg_id_response = await send_private_message(nick, BOXES_INFO_MESSAGE)
    if msg_id_response:
        await delete_message_via_api(msg_id_response)


async def cmd_open_box(nick: str, msg_id: str):
    """Открыть бокс для пользователя"""
    try:
        # Проверить что пользователь зарегистрирован
        user = await craftcards_api.get_user(nick)
        
        if not user:
            msg = (
                "⚠️ Ты еще не зарегистрирован в CraftCards!\n"
                "Напиши !регистрация чтобы начать."
            )
            msg_id_response = await send_private_message(nick, msg)
            if msg_id_response:
                await delete_message_via_api(msg_id_response)
            return
        
        # Открыть бокс через API
        # POST /api/users/{vk_id}/boxes
        import httpx
        from chatbot.constants.cnst_Server import CRAFTCARDS_API_URL, HTTP_TIMEOUT
        
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(
                f"{CRAFTCARDS_API_URL}/api/users/{nick}/boxes",
                json={
                    "vk_id": nick,
                    "nickname": nick,
                    "count": 1,
                    "rarity": 0  # Стандартный бокс
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Получить результат открытия
                results = result.get('results', [])
                if results:
                    last_result = results[-1]
                    box_type = last_result.get('box_type', 'Стандарт')
                    count = last_result.get('count', 0)
                    rare_drops = last_result.get('rare_drops', '')
                    merges = last_result.get('merges', '')
                    ac_won = last_result.get('ac_won', 0)
                    
                    # Формировать ответ
                    lines = [
                        f"📦 Ты открыл {box_type} бокс!",
                        f"🎴 Получено карт: {count}",
                    ]
                    
                    if rare_drops:
                        lines.append(f"✨ Редкие карты: {rare_drops}")
                    
                    if merges:
                        lines.append(f"🔀 Мерж: {merges}")
                    
                    lines.append(f"💎 AC: +{ac_won}")
                    
                    msg = "\n".join(lines)
                else:
                    msg = "📦 Бокс открыт! Напиши !карты чтобы увидеть инвентарь."
            else:
                msg = "⚠️ Ошибка при открытии бокса. Попробуй позже."
        
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)
            
    except Exception as e:
        print(f"[Handler] Error in !open: {e}")
        msg = "⚠️ Произошла ошибка при открытии бокса."
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)


async def cmd_new_stream(nick: str, msg_id: str):
    """Начать новый стрим (сбросить счётчики боксов всех пользователей)"""
    try:
        import httpx
        from chatbot.constants.cnst_Server import CRAFTCARDS_API_URL, HTTP_TIMEOUT
        
        # Вызываем API для сброса дня
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(
                f"{CRAFTCARDS_API_URL}/api/stream/start-day"
            )
            
            if response.status_code == 200:
                result = response.json()
                users_reset = result.get('users_reset', 0)
                
                msg = (
                    f"🔄 Начат новый стрим!\n"
                    f"Счётчики боксов сброшены для {users_reset} пользователей.\n"
                    f"Первый бокс = 6 карт (4 + 1*2)"
                )
            else:
                msg = "⚠️ Ошибка при сбросе стрима. Попробуй через админку."
        
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)
            
    except Exception as e:
        print(f"[Handler] Error in !newstream: {e}")
        msg = "⚠️ Произошла ошибка при сбросе стрима."
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)


async def cmd_viewer_time(nick: str, msg_id: str):
    """Показать время на стриме и AC бонусы"""
    try:
        # Получить vk_id пользователя
        uid = await ensure_user_exists(nick, skip_greeting=True)
        vk_id = int(uid) if uid else None
        
        if not vk_id:
            msg = "⚠️ Ты не зарегистрирован. Напиши !регистрация"
            msg_id_response = await send_private_message(nick, msg)
            if msg_id_response:
                await delete_message_via_api(msg_id_response)
            return
        
        # Получить информацию о сессии
        from chatbot.services.viewer_tracker import ViewerTracker
        from chatbot.services.vk_api_client import VKLiveAPIClient
        from chatbot.constants.cnst_VK import VK_LIVE_API_TOKEN, VK_LIVE_CHANNEL_NAME
        
        vk_api = VKLiveAPIClient(VK_LIVE_API_TOKEN, VK_LIVE_CHANNEL_NAME)
        tracker = ViewerTracker(vk_api)
        
        session_info = await tracker.get_viewer_session_info(vk_id)
        
        if not session_info:
            msg = (
                f"⏱ Ты пока не заходил на стрим в этой сессии.\n"
                f"Зайди на трансляцию чтобы начать отсчёт времени!"
            )
        else:
            total_minutes = session_info["total_minutes"]
            ac_earned = session_info["ac_earned"]
            milestones = session_info["milestones"]
            
            # Получить текущий AC бонус
            current_ac_bonus = tracker.get_ac_bonus(total_minutes)
            
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            
            milestones_str = ", ".join([f"{m} мин" for m in sorted(milestones)]) if milestones else "нет"
            
            msg = (
                f"⏱ Твоя сессия на стриме:\n"
                f"Время: {hours}ч {minutes}м\n"
                f"AC заработано: {ac_earned}\n"
                f"Текущий бонус: +{current_ac_bonus} AC / 5 мин\n"
                f"Milestones: {milestones_str}"
            )
        
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)
            
    except Exception as e:
        print(f"[Handler] Error in !time: {e}")
        msg = "⚠️ Произошла ошибка при получении информации о сессии."
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)


async def cmd_viewer_bonuses(nick: str, msg_id: str):
    """Показать достигнутые milestones"""
    try:
        # Получить vk_id пользователя
        uid = await ensure_user_exists(nick, skip_greeting=True)
        vk_id = int(uid) if uid else None
        
        if not vk_id:
            msg = "⚠️ Ты не зарегистрирован. Напиши !регистрация"
            msg_id_response = await send_private_message(nick, msg)
            if msg_id_response:
                await delete_message_via_api(msg_id_response)
            return
        
        # Получить информацию о сессии
        from chatbot.services.viewer_tracker import ViewerTracker
        from chatbot.services.vk_api_client import VKLiveAPIClient
        from chatbot.constants.cnst_VK import VK_LIVE_API_TOKEN, VK_LIVE_CHANNEL_NAME
        
        vk_api = VKLiveAPIClient(VK_LIVE_API_TOKEN, VK_LIVE_CHANNEL_NAME)
        tracker = ViewerTracker(vk_api)
        
        session_info = await tracker.get_viewer_session_info(vk_id)
        
        if not session_info:
            msg = "⏱ Ты пока не заходил на стрим в этой сессии."
        else:
            total_minutes = session_info["total_minutes"]
            milestones = session_info["milestones"]
            
            # Все доступные milestones
            all_milestones = {
                15: "📦 +1 стандартный бокс",
                30: "💰 +3 AC",
                60: "🎁 +1 элитный бокс",
                180: "🏆 Бонус ветерана (стандартный + элитный бокс + PA заряд)"
            }
            
            lines = ["🎁 Твои бонусы на стриме:\n"]
            
            for minutes, description in sorted(all_milestones.items()):
                status = "✅" if minutes in milestones else "⬜"
                lines.append(f"{status} {minutes} мин: {description}")
            
            # Показать следующий milestone
            next_milestone = None
            for minutes in sorted(all_milestones.keys()):
                if minutes not in milestones:
                    next_milestone = minutes
                    break
            
            if next_milestone:
                remaining = next_milestone - total_minutes
                if remaining > 0:
                    lines.append(f"\n⏳ До следующего бонуса: {remaining} мин")
                else:
                    lines.append(f"\n✅ Все бонусы получены!")
            
            msg = "\n".join(lines)
        
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)
            
    except Exception as e:
        print(f"[Handler] Error in !bonuses: {e}")
        msg = "⚠️ Произошла ошибка при получении бонусов."
        msg_id_response = await send_private_message(nick, msg)
        if msg_id_response:
            await delete_message_via_api(msg_id_response)

