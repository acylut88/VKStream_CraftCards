"""
Клиент для взаимодействия с API CraftCards
"""
import httpx
from typing import Optional, Dict, List, Any
from chatbot.constants.cnst_Server import CRAFTCARDS_API_URL, HTTP_TIMEOUT


class CraftCardsAPIClient:
    """Клиент для общения с CraftCards API"""
    
    def __init__(self, base_url: str = CRAFTCARDS_API_URL):
        self.base_url = base_url
        self.timeout = HTTP_TIMEOUT
    
    async def get_user(self, vk_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/users/{vk_id}")
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"[CraftCardsAPI] Error getting user: {e}")
            return None
    
    async def get_user_inventory(self, vk_id: str) -> Optional[Dict[str, Any]]:
        """Получить инвентарь пользователя"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/users/{vk_id}/inventory")
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"[CraftCardsAPI] Error getting inventory: {e}")
            return None
    
    async def get_analytics(self) -> Optional[Dict[str, Any]]:
        """Получить общую аналитику"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/analytics")
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"[CraftCardsAPI] Error getting analytics: {e}")
            return None
    
    async def get_leaderboard(self, session_id: int, event_type: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Получить лидерборд"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/stream/leaderboard/{session_id}/{event_type}",
                    params={"limit": limit}
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"[CraftCardsAPI] Error getting leaderboard: {e}")
            return None
    
    async def get_ac_leaderboard(self, session_id: int, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Получить AC лидерборд"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/stream/leaderboard/{session_id}/ac/top",
                    params={"limit": limit}
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"[CraftCardsAPI] Error getting AC leaderboard {e}")
            return None
    
    async def get_active_session(self) -> Optional[Dict[str, Any]]:
        """Получить текущую активную сессию"""
        try:
            # Сначала получаем все сессии и фильтруем активную
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/stream/sessions")
                if response.status_code == 200:
                    sessions = response.json()
                    # Найти активную сессию (предполагаем что последняя активная)
                    for session in sessions:
                        if session.get('status') == 'active':
                            return session
                    # Если нет активных, возвращаем последнюю
                    return sessions[-1] if sessions else None
                return None
        except Exception as e:
            print(f"[CraftCardsAPI] Error getting active session: {e}")
            return None
    
    async def create_user(self, vk_id: str, nickname: str, stars: int = 3, pa_charges: int = 0) -> bool:
        """Создать нового пользователя"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/users",
                    json={
                        "vk_id": vk_id,
                        "nickname": nickname,
                        "stars": stars,
                        "pa_charges": pa_charges
                    }
                )
                return response.status_code in [200, 201]
        except Exception as e:
            print(f"[CraftCardsAPI] Error creating user: {e}")
            return False


# Глобальный экземпляр клиента
craftcards_api = CraftCardsAPIClient()
