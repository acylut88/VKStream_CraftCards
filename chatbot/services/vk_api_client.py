"""
VK Video Live API клиент для получения списка зрителей
"""
import httpx
from typing import Dict, List, Optional
from datetime import datetime


class VKLiveAPIClient:
    """Клиент для VK Video Live API"""
    
    def __init__(self, auth_token: str, channel_name: str):
        self.base_url = "https://api.live.vkvideo.ru"
        self.auth_token = auth_token
        self.channel_name = channel_name
        
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {auth_token}",
            "Connection": "keep-alive",
            "Origin": "https://live.vkvideo.ru",
            "Referer": f"https://live.vkvideo.ru/{channel_name}/stream/default/only-chat",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "X-App": "streams_web",
            "X-Referer": "vkvideo.ru",
            "X-Trans-Via": "chat"
        }
    
    async def get_chat_users(self, with_bans: bool = True) -> Optional[Dict]:
        """
        Получить список всех пользователей в чате
        
        Возвращает:
        {
            "users": [{"nick": "...", "id": 123, "name": "..."}],
            "owner": {...},
            "moderators": [...]
        }
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/v1/channel/{self.channel_name}/stream/slot/default/chat/user/",
                    params={"with_bans": with_bans},
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data")
                else:
                    print(f"[VK API] Error: {response.status_code}")
                    return None
        except Exception as e:
            print(f"[VK API] Exception: {e}")
            return None
    
    async def get_viewers_list(self) -> List[Dict]:
        """
        Получить упрощённый список зрителей
        
        Возвращает:
        [
            {"vk_id": 123, "nickname": "User1", "name": "User1", "avatar_url": "..."},
            ...
        ]
        """
        data = await self.get_chat_users()
        
        if not data:
            return []
        
        viewers = []
        
        # Добавляем обычных пользователей
        for user in data.get("users", []):
            viewers.append({
                "vk_id": user.get("id"),
                "nickname": user.get("nick"),
                "name": user.get("name"),
                "avatar_url": user.get("avatarUrl"),
                "is_verified": user.get("isVerifiedStreamer", False)
            })
        
        # Добавляем модераторов
        for mod in data.get("moderators", []):
            viewers.append({
                "vk_id": mod.get("id"),
                "nickname": mod.get("nick"),
                "name": mod.get("name"),
                "avatar_url": mod.get("avatarUrl"),
                "is_moderator": True
            })
        
        # Добавляем владельца (стримера) если нужно
        owner = data.get("owner")
        if owner:
            viewers.append({
                "vk_id": owner.get("id"),
                "nickname": owner.get("nick"),
                "name": owner.get("name"),
                "avatar_url": owner.get("avatarUrl"),
                "is_owner": True
            })
        
        return viewers
    
    async def get_user_by_nickname(self, nickname: str) -> Optional[Dict]:
        """Найти пользователя по никнейму"""
        viewers = await self.get_viewers_list()
        
        for viewer in viewers:
            if viewer["nickname"].lower() == nickname.lower():
                return viewer
        
        return None
