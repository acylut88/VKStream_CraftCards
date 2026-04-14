"""
Утилиты для отправки сообщений в чат VK
"""
import httpx
from typing import Optional
from chatbot.constants.cnst_VK import HEADERS
from chatbot.constants.cnst_Server import HTTP_TIMEOUT


API_URL = "https://vkvideo.ru/api"


async def send_private_message(nickname: str, message: str) -> Optional[str]:
    """
    Отправить личное сообщение в чат VK
    Возвращает ID сообщения или None при ошибке
    """
    try:
        # Формируем сообщение с упоминанием пользователя
        full_message = f"@{nickname}, {message}"
        
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(
                f"{API_URL}/chat/message",
                json={
                    "text": full_message,
                    "private_to": nickname
                },
                headers=HEADERS
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("message_id")
            return None
    except Exception as e:
        print(f"[BotUtils] Error sending message: {e}")
        return None


async def delete_message_via_api(message_id: str, skip_author_check: bool = False) -> bool:
    """
    Удалить сообщение из чата через API
    """
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.delete(
                f"{API_URL}/chat/message/{message_id}",
                headers=HEADERS
            )
            return response.status_code == 200
    except Exception as e:
        print(f"[BotUtils] Error deleting message: {e}")
        return False
