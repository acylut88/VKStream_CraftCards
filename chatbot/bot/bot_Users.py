"""
Управление пользователями в чат-боте
"""
from datetime import datetime
from sqlalchemy import select
from chatbot.database.database import get_db, ChatUser
from chatbot.services.craftcards_api import craftcards_api
from chatbot.constants.cnst_Bot import WELCOME_MESSAGE


async def ensure_user_exists(nick: str, skip_greeting: bool = False) -> int:
    """
    Проверить是否存在 пользователь в кеше чат-бота
    Если нет - создать и попробовать зарегистрировать в CraftCards
    Возвращает ID пользователя или None
    """
    async with get_db() as db:
        # Проверить в кеше
        result = await db.execute(select(ChatUser).filter(ChatUser.nick == nick))
        user = result.scalar_one_or_none()
        
        if not user:
            # Создать нового пользователя
            user = ChatUser(
                nick=nick,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
            db.add(user)
            await db.flush()  # Получить ID
            
            # Попробовать зарегистрировать в CraftCards
            try:
                await craftcards_api.create_user(
                    vk_id=str(user.id),  # Используем локальный ID как vk_id
                    nickname=nick,
                    stars=3,  # Welcome-бонус
                    pa_charges=0
                )
                user.is_registered = True
                user.vk_id = str(user.id)
                await db.flush()
                
                if not skip_greeting:
                    print(f"[Users] New user registered: {nick}")
            except Exception as e:
                print(f"[Users] Failed to register in CraftCards: {e}")
        else:
            # Обновить last_seen
            user.last_seen = datetime.utcnow()
            await db.flush()
        
        return user.id


async def get_user_by_nick(nick: str) -> ChatUser:
    """Получить пользователя по нику"""
    async with get_db() as db:
        result = await db.execute(select(ChatUser).filter(ChatUser.nick == nick))
        return result.scalar_one_or_none()


async def get_user_by_vk_id(vk_id: str) -> ChatUser:
    """Получить пользователя по VK ID"""
    async with get_db() as db:
        result = await db.execute(select(ChatUser).filter(ChatUser.vk_id == vk_id))
        return result.scalar_one_or_none()


async def link_user_to_craftcards(nick: str, vk_id: str) -> bool:
    """Привязать пользователя к CraftCards"""
    async with get_db() as db:
        result = await db.execute(select(ChatUser).filter(ChatUser.nick == nick))
        user = result.scalar_one_or_none()
        
        if user:
            user.vk_id = vk_id
            user.is_registered = True
            await db.flush()
            return True
        return False
