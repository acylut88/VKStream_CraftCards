"""
ViewerTracker - трекинг зрителей, AC бонусы и milestones
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, text
import json

from chatbot.services.vk_api_client import VKLiveAPIClient
from chatbot.services.craftcards_api import craftcards_api
from chatbot.database.database import get_db, get_db_cm
from chatbot.constants.cnst_Server import CRAFTCARDS_API_URL, HTTP_TIMEOUT


class ViewerTracker:
    """Трекинг зрителей на стриме"""
    
    def __init__(self, vk_api: VKLiveAPIClient):
        self.vk_api = vk_api
        self.poll_interval = 300  # 5 минут
        self.is_running = False
        
        # AC бонусы (прогрессивная система)
        self.ac_bonus_tiers = {
            0: 5,    # 0+ мин:   +5 AC / 5 мин
            30: 10,  # 30+ мин:  +10 AC / 5 мин
            60: 20,  # 60+ мин:  +20 AC / 5 мин
            120: 30, # 120+ мин: +30 AC / 5 мин
            180: 50  # 180+ мин: +50 AC / 5 мин
        }
        
        # Milestones (одноразовые бонусы)
        self.milestones = {
            15: {"type": "box", "count": 1, "name": "Стандартный бокс"},
            30: {"type": "ac", "count": 3, "name": "+3 AC"},
            60: {"type": "elite_box", "count": 1, "name": "Элитный бокс"},
            180: {
                "type": "mixed",
                "standard_box": 1,
                "elite_box": 1,
                "pa_charge": 1,
                "name": "Бонус ветерана (180 мин)"
            }
        }
    
    def get_ac_bonus(self, minutes: int) -> int:
        """Получить AC бонус по времени на стриме"""
        bonus = 5  # По умолчанию
        
        for threshold, ac in sorted(self.ac_bonus_tiers.items()):
            if minutes >= threshold:
                bonus = ac
            else:
                break
        
        return bonus
    
    async def get_current_ac_bonus(self, minutes: int) -> int:
        """Получить текущий AC бонус"""
        return self.get_ac_bonus(minutes)
    
    async def process_viewer_poll(self):
        """Основной цикл опроса зрителей"""
        try:
            print(f"[ViewerTracker] Polling viewers...")
            
            # Получить текущих зрителей из VK API
            viewers = await self.vk_api.get_viewers_list()
            
            if not viewers:
                print("[ViewerTracker] No viewers found")
                return
            
            print(f"[ViewerTracker] Found {len(viewers)} viewers")
            
            # Обработать каждого зрителя
            async with get_db() as db:
                for viewer in viewers:
                    vk_id = viewer["vk_id"]
                    nickname = viewer["nickname"]
                    
                    await self._process_viewer(db, vk_id, nickname)
                
                await db.flush()
        
        except Exception as e:
            print(f"[ViewerTracker] Error in poll: {e}")
    
    async def _process_viewer(self, db, vk_id: int, nickname: str):
        """Обработать одного зрителя"""
        try:
            from chatbot.database.database import ViewerSession
            
            # Найти сессию зрителя
            result = await db.execute(
                select(ViewerSession).filter(ViewerSession.vk_id == vk_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                # Новый зритель - создать сессию
                print(f"[ViewerTracker] New viewer: {nickname} ({vk_id})")
                session = ViewerSession(
                    vk_id=vk_id,
                    nickname=nickname,
                    session_start=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    total_minutes=0,
                    ac_earned=0,
                    milestones_achieved="[]"
                )
                db.add(session)
                
                # Зарегистрировать в CraftCards если не зарегистрирован
                await self._ensure_registered(vk_id, nickname)
            else:
                # Обновить сессию
                old_minutes = session.total_minutes
                
                # Посчитать прошедшее время
                time_diff = (datetime.utcnow() - session.last_seen).total_seconds() / 60.0
                session.total_minutes += time_diff
                session.last_seen = datetime.utcnow()
                session.nickname = nickname  # Обновить никнейм
                
                # Начислить AC за прошедшее время
                await self._award_ac_for_time(db, session, old_minutes)
                
                # Проверить milestones
                await self._check_milestones(db, session, old_minutes)
        
        except Exception as e:
            print(f"[ViewerTracker] Error processing viewer {nickname}: {e}")
    
    async def _award_ac_for_time(self, db, session, old_minutes: int):
        """Начислить AC за время на стриме"""
        try:
            # Получить AC бонус для текущего времени
            ac_bonus = self.get_ac_bonus(session.total_minutes)
            
            # Начислить AC через CraftCards API
            import httpx
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(
                    f"{CRAFTCARDS_API_URL}/api/users/{session.vk_id}/update",
                    json={"ac_balance": ac_bonus}
                )
                
                if response.status_code == 200:
                    session.ac_earned += ac_bonus
                    print(f"[ViewerTracker] {session.nickname}: +{ac_bonus} AC ({session.total_minutes:.0f} min)")
                else:
                    print(f"[ViewerTracker] Failed to award AC to {session.nickname}")
        
        except Exception as e:
            print(f"[ViewerTracker] Error awarding AC: {e}")
    
    async def _check_milestones(self, db, session, old_minutes: int):
        """Проверить достижение milestones"""
        try:
            achieved = json.loads(session.milestones_achieved)
            
            for minutes_threshold, milestone_info in self.milestones.items():
                # Проверить что milestone ещё не достигнут
                if minutes_threshold in achieved:
                    continue
                
                # Проверить что зритель прошёл порог
                if session.total_minutes >= minutes_threshold:
                    # Отметить как достигнутый
                    achieved.append(minutes_threshold)
                    session.milestones_achieved = json.dumps(achieved)
                    
                    # Выдать бонус
                    await self._award_milestone(session.vk_id, session.nickname, milestone_info)
                    
                    print(f"[ViewerTracker] {session.nickname} reached milestone: {minutes_threshold} min")
        
        except Exception as e:
            print(f"[ViewerTracker] Error checking milestones: {e}")
    
    async def _award_milestone(self, vk_id: int, nickname: str, milestone_info: Dict):
        """Выдать бонус за milestone"""
        try:
            import httpx
            
            milestone_type = milestone_info["type"]
            count = milestone_info.get("count", 1)
            name = milestone_info["name"]
            
            if milestone_type == "box":
                # Стандартный бокс
                async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                    response = await client.post(
                        f"{CRAFTCARDS_API_URL}/api/users/{vk_id}/boxes",
                        json={
                            "vk_id": vk_id,
                            "nickname": nickname,
                            "count": count,
                            "rarity": 0
                        }
                    )
                    if response.status_code == 200:
                        print(f"[ViewerTracker] Milestone: {nickname} got {count} standard box(es)")
            
            elif milestone_type == "ac":
                # AC бонус
                async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                    response = await client.post(
                        f"{CRAFTCARDS_API_URL}/api/users/{vk_id}/update",
                        json={"ac_balance": count}
                    )
                    if response.status_code == 200:
                        print(f"[ViewerTracker] Milestone: {nickname} got +{count} AC")
            
            elif milestone_type == "elite_box":
                # Элитный бокс
                async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                    response = await client.post(
                        f"{CRAFTCARDS_API_URL}/api/users/{vk_id}/boxes",
                        json={
                            "vk_id": vk_id,
                            "nickname": nickname,
                            "count": count,
                            "rarity": 1
                        }
                    )
                    if response.status_code == 200:
                        print(f"[ViewerTracker] Milestone: {nickname} got {count} elite box(es)")
            
            elif milestone_type == "pa_charge":
                # PA заряд
                async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                    response = await client.post(
                        f"{CRAFTCARDS_API_URL}/api/users/{vk_id}/update",
                        json={"pa_charges": count}
                    )
                    if response.status_code == 200:
                        print(f"[ViewerTracker] Milestone: {nickname} got {count} PA charge(s)")
            
            elif milestone_type == "mixed":
                # Комбинированный бонус (180 мин)
                standard_box = milestone_info.get("standard_box", 0)
                elite_box = milestone_info.get("elite_box", 0)
                pa_charge = milestone_info.get("pa_charge", 0)
                
                async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                    # Стандартный бокс
                    if standard_box > 0:
                        await client.post(
                            f"{CRAFTCARDS_API_URL}/api/users/{vk_id}/boxes",
                            json={
                                "vk_id": vk_id,
                                "nickname": nickname,
                                "count": standard_box,
                                "rarity": 0
                            }
                        )
                    
                    # Элитный бокс
                    if elite_box > 0:
                        await client.post(
                            f"{CRAFTCARDS_API_URL}/api/users/{vk_id}/boxes",
                            json={
                                "vk_id": vk_id,
                                "nickname": nickname,
                                "count": elite_box,
                                "rarity": 1
                            }
                        )
                    
                    # PA заряд
                    if pa_charge > 0:
                        await client.post(
                            f"{CRAFTCARDS_API_URL}/api/users/{vk_id}/update",
                            json={"pa_charges": pa_charge}
                        )
                
                print(f"[ViewerTracker] Milestone: {nickname} got mixed bonus (180 min)")
        
        except Exception as e:
            print(f"[ViewerTracker] Error awarding milestone: {e}")
    
    async def _ensure_registered(self, vk_id: int, nickname: str):
        """Убедиться что зритель зарегистрирован в CraftCards"""
        try:
            # Проверить существует ли пользователь
            user = await craftcards_api.get_user(str(vk_id))
            
            if not user:
                # Зарегистрировать с vk_id
                success = await craftcards_api.create_user(
                    vk_id=str(vk_id),
                    nickname=nickname,
                    stars=3,  # Welcome-бонус
                    pa_charges=0
                )
                
                if success:
                    print(f"[ViewerTracker] Registered {nickname} ({vk_id})")
                else:
                    print(f"[ViewerTracker] Failed to register {nickname} ({vk_id})")
        
        except Exception as e:
            print(f"[ViewerTracker] Error ensuring registration: {e}")
    
    async def get_viewer_session_info(self, vk_id: int) -> Optional[Dict]:
        """Получить информацию о сессии зрителя"""
        try:
            async with get_db() as db:
                from chatbot.database.database import ViewerSession
                
                result = await db.execute(
                    select(ViewerSession).filter(ViewerSession.vk_id == vk_id)
                )
                session = result.scalar_one_or_none()
                
                if not session:
                    return None
                
                return {
                    "vk_id": session.vk_id,
                    "nickname": session.nickname,
                    "total_minutes": int(session.total_minutes),
                    "ac_earned": session.ac_earned,
                    "milestones": json.loads(session.milestones_achieved),
                    "session_start": session.session_start.isoformat()
                }
        
        except Exception as e:
            print(f"[ViewerTracker] Error getting session info: {e}")
            return None
