"""
Расширенное REST API для админ-панели React + ChatBot
"""
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import asynccontextmanager
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timedelta
import json
import asyncio
import threading

from database import DatabaseManager
from main import db, engine, process_lootbox_opening, game_logs

# --- ChatBot Integration ---
CHATBOT_ENABLED = True
chatbot_thread = None

def run_chatbot_in_thread():
    """Запуск чат-бота в отдельном потоке с собственным event loop"""
    import sys
    import warnings
    
    # Игнорировать deprecation warnings для ProactorEventLoop
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    
    # Установить ProactorEventLoop для нового потока
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        from chatbot.database.database import init_db as chatbot_init_db
        from chatbot.bot.bot_Main import bot_task
        
        # Инициализируем БД
        loop.run_until_complete(chatbot_init_db())
        print("[ChatBot] Database initialized in thread")
        
        # Запускаем чат-бот
        loop.run_until_complete(bot_task())
    except Exception as e:
        print(f"[ChatBot] Error in thread: {e}")
    finally:
        loop.close()

async def start_chatbot_background():
    """Запуск чат-бота как фоновой задачи"""
    global chatbot_thread
    
    if not CHATBOT_ENABLED:
        print("[ChatBot] Disabled in configuration")
        return
    
    try:
        print("[ChatBot] Starting in separate thread...")
        
        # Запускаем в отдельном потоке чтобы избежать конфликта event loops
        chatbot_thread = threading.Thread(
            target=run_chatbot_in_thread,
            daemon=True,
            name="ChatBotThread"
        )
        chatbot_thread.start()
        print("[ChatBot] Background thread started")
        
    except Exception as e:
        print(f"[ChatBot] Error starting chatbot: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler для startup/shutdown"""
    # Startup
    print("[Startup] Starting VKStream CraftCards API...")
    await start_chatbot_background()
    yield
    # Shutdown
    print("[Shutdown] Shutting down VKStream CraftCards API...")
    if chatbot_thread and chatbot_thread.is_alive():
        print("[ChatBot] Waiting for chatbot thread to finish...")
        # ChatBot thread daemon - завершится автоматически
        chatbot_thread.join(timeout=2.0)
    print("[Shutdown] Complete")

app = FastAPI(title="VKStream API", version="1.0", lifespan=lifespan)

# --- CORS для React фронтенда ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic модели ---

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    vk_id: str
    nickname: str
    stars: int
    pa_charges: int
    pa_active_today: int
    std_boxes_today: int
    elite_boxes_today: int
    ac_balance: int
    ac_today: int

class BoxRequest(BaseModel):
    vk_id: str
    nickname: Optional[str] = None
    count: int = 1
    rarity: int = 1  # 1, 2, или 3 для элитных боксов

class UserUpdateRequest(BaseModel):
    stars: Optional[int] = None
    pa_charges: Optional[int] = None
    ac_balance: Optional[int] = None
    nickname: Optional[str] = None

class UserCreateRequest(BaseModel):
    vk_id: str
    nickname: str
    stars: int = 3
    pa_charges: int = 0

class LogResponse(BaseModel):
    timestamp: str
    nickname: str
    box_type: str
    count: int
    rare_drops: str
    merges: str
    ac_won: int

# Stream Events Models
class StreamSessionRequest(BaseModel):
    event_type: str  # 'card' | 'ac_farming' | 'both'
    stream_date: str = None
    stream_name: Optional[str] = None

class StreamSessionResponse(BaseModel):
    session_id: int
    stream_date: str
    stream_name: Optional[str]
    event_type: str
    status: str
    created_at: str

class LeaderboardEntry(BaseModel):
    vk_id: str
    nickname: Optional[str]
    rank: Optional[int]
    current_value: int
    card_distribution: Optional[str]

class RareDropResponse(BaseModel):
    vk_id: str
    nickname: str
    card_type: str
    card_level: int
    probability: float
    timestamp: str
    box_type: str

class OverlayWinnerResponse(BaseModel):
    winner_vk_id: str
    winner_nickname: str
    card_type: str
    card_level: int
    timestamp: str

# --- MANAGERS (для WebSocket) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# --- API ENDPOINTS ---

@app.get("/api/users", response_model=List[UserResponse])
async def get_users():
    """Список всех пользователей"""
    users = await db.get_all_users_admin()
    return [dict(u) for u in users]

@app.get("/api/users/{vk_id}", response_model=UserResponse)
async def get_user(vk_id: str):
    """Информация конкретного пользователя"""
    user = await db.get_user(vk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)

@app.post("/api/users", response_model=UserResponse)
async def create_user_endpoint(request: UserCreateRequest):
    """Создать нового пользователя"""
    try:
        user = await db.create_user(
            vk_id=request.vk_id,
            nickname=request.nickname,
            stars=request.stars,
            pa_charges=request.pa_charges
        )
        
        await manager.broadcast({
            "type": "user_created",
            "vk_id": request.vk_id,
            "nickname": request.nickname,
            "timestamp": datetime.now().isoformat()
        })
        
        return dict(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create user")

@app.post("/api/users/{vk_id}/update")
async def update_user(vk_id: str, data: UserUpdateRequest):
    """Обновить данные пользователя"""
    updates_made = False
    
    if data.nickname:
        await db.rename_user(vk_id, data.nickname)
        updates_made = True
    
    if data.stars is not None:
        current_user = await db.get_user(vk_id)
        change = data.stars - current_user['stars']
        await db.update_user_field(vk_id, "stars", change)
        updates_made = True
    
    if data.pa_charges is not None:
        current_user = await db.get_user(vk_id)
        change = data.pa_charges - current_user['pa_charges']
        await db.update_user_field(vk_id, "pa_charges", change)
        updates_made = True
    
    if data.ac_balance is not None:
        current_user = await db.get_user(vk_id)
        change = data.ac_balance - current_user['ac_balance']
        await db.update_ac(vk_id, change)
        updates_made = True
    
    if updates_made:
        await manager.broadcast({
            "type": "user_updated",
            "vk_id": vk_id,
            "timestamp": datetime.now().isoformat()
        })
    
    return {"status": "updated" if updates_made else "no_changes"}

@app.post("/api/users/{vk_id}/boxes")
async def give_boxes(vk_id: str, request: BoxRequest):
    """
    Начислить N боксов пользователю
    rarity: 1, 2, 3 для элитных боксов (по уровню редкости)
    """
    user = await db.get_user(vk_id)
    if not user:
        user = await db.get_user(vk_id, request.nickname or "Unknown")
    
    results = []
    for i in range(request.count):
        # Для элитных боксов используем is_elite=True и соответствующую рарность
        if request.rarity in [1, 2, 3]:
            # Элитные боксы
            result = await process_lootbox_opening(vk_id, user['nickname'], is_elite=True)
            result['box_type'] = f"Элитный (рарность {request.rarity})"
        else:
            # Стандартные боксы
            result = await process_lootbox_opening(vk_id, user['nickname'], is_elite=False)
            result['box_type'] = "Стандарт"
        
        results.append(result)
    
    await manager.broadcast({
        "type": "boxes_added",
        "vk_id": vk_id,
        "count": request.count,
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "success", "boxes_added": request.count, "results": results}

@app.get("/api/users/{vk_id}/inventory")
async def get_user_inventory(vk_id: str):
    """Инвентарь пользователя"""
    inventories = await db.get_all_inventories_grouped()
    inventory = inventories.get(vk_id, [])
    return {"vk_id": vk_id, "cards": inventory}

@app.delete("/api/users/{vk_id}")
async def delete_user(vk_id: str):
    """Удалить пользователя полностью"""
    await db.delete_user_completely(vk_id)
    
    await manager.broadcast({
        "type": "user_deleted",
        "vk_id": vk_id,
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "deleted"}

@app.get("/api/analytics")
async def get_analytics():
    """Аналитика по игре"""
    users = await db.get_all_users_admin()
    logs = await db.get_recent_logs(1000)
    
    # Базовая статистика
    total_users = len(users)
    total_boxes = sum(u['std_boxes_today'] + u['elite_boxes_today'] for u in users)
    total_ac = sum(u['ac_today'] for u in users)
    
    # Статистика по боксам
    box_stats = {
        "std_count": sum(u['std_boxes_today'] for u in users),
        "elite_count": sum(u['elite_boxes_today'] for u in users),
    }
    
    # Активные пользователи (открыли хотя бы 1 бокс)
    active_users = sum(1 for u in users if u['std_boxes_today'] > 0 or u['elite_boxes_today'] > 0)
    
    # Top players (по AC или весу)
    top_players = sorted(
        [(u['nickname'], u['ac_balance'], u['std_boxes_today'] + u['elite_boxes_today']) for u in users],
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    # Средние значения
    avg_boxes_per_user = total_boxes / total_users if total_users > 0 else 0
    avg_ac_per_user = total_ac / total_users if total_users > 0 else 0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_boxes": total_boxes,
        "box_stats": box_stats,
        "total_ac": total_ac,
        "avg_boxes_per_user": round(avg_boxes_per_user, 2),
        "avg_ac_per_user": round(avg_ac_per_user, 2),
        "top_players": [{"nickname": p[0], "ac": p[1], "boxes": p[2]} for p in top_players],
        "logs_count": len(logs)
    }

@app.get("/api/logs", response_model=List[LogResponse])
async def get_logs(limit: int = Query(100, le=1000)):
    """Получить логи событий"""
    logs = await db.get_recent_logs(limit)
    return [dict(log) for log in logs]

@app.get("/api/stats/timeline")
async def get_timeline_stats(days: int = Query(7, ge=1, le=30)):
    """Статистика по дням"""
    logs = await db.get_recent_logs(10000)
    
    # Группируем по датам
    timeline = {}
    for log in logs:
        # Допустим, timestamp в формате "HH:MM:SS", нужно обработать
        date_key = "today"  # Упрощённо - можно расширить
        if date_key not in timeline:
            timeline[date_key] = {
                "boxes": 0,
                "ac": 0,
                "rare_drops": 0,
                "merges": 0
            }
        timeline[date_key]["boxes"] += 1
        timeline[date_key]["ac"] += log.get('ac_won', 0) if log else 0
        if log.get('rare_drops'):
            timeline[date_key]["rare_drops"] += len(log['rare_drops'].split(","))
        if log.get('merges'):
            timeline[date_key]["merges"] += len(log['merges'].split(","))
    
    return timeline

@app.post("/api/stream/finish")
async def finish_stream():
    """Завершить стрим (сброс дня, экспорт CSV)"""
    from main import finish_stream_logic
    
    result = await finish_stream_logic()
    
    await manager.broadcast({
        "type": "stream_finished",
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "stream_finished"}

@app.post("/api/stream/clear-all")
async def clear_all_data():
    """Очистить ВСЮ базу (опасно!)"""
    await db.clear_full_database()
    
    await manager.broadcast({
        "type": "database_cleared",
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "database_cleared"}

# --- STREAM EVENTS ENDPOINTS ---

@app.post("/api/stream/start-day")
async def start_stream_day():
    """Сброс pa_active_today для ВСЕХ игроков перед началом стрима"""
    try:
        await db.reset_pa_active_today_all()
        users = await db.get_all_users_admin()
        
        await manager.broadcast({
            "type": "stream_started",
            "users_count": len(users),
            "timestamp": datetime.now().isoformat()
        })
        
        return {"status": "success", "users_reset": len(users)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stream/session/create", response_model=StreamSessionResponse)
async def create_stream_session(request: StreamSessionRequest):
    """Создать новую потоковую сессию"""
    try:
        from datetime import date
        stream_date = request.stream_date or str(date.today())
        
        session_id = await db.create_stream_session(
            event_type=request.event_type,
            stream_date=stream_date,
            stream_name=request.stream_name
        )
        
        # Сбросить pa_active_today для всех игроков
        await db.reset_pa_active_today_all()
        
        await manager.broadcast({
            "type": "session_created",
            "session_id": session_id,
            "event_type": request.event_type,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "session_id": session_id,
            "stream_date": stream_date,
            "stream_name": request.stream_name,
            "event_type": request.event_type,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stream/session/{session_id}/finish")
async def finish_stream_session(session_id: int):
    """Завершить потоковую сессию"""
    try:
        await db.finish_stream_session(session_id)
        
        await manager.broadcast({
            "type": "session_finished",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream/leaderboard/{session_id}/{event_type}")
async def get_event_leaderboard(session_id: int, event_type: str, limit: int = Query(10, ge=1, le=50)):
    """Получить текущий лидерборд для события"""
    try:
        leaderboard = await db.get_current_leaderboard(session_id, event_type, limit)
        
        # Добавляем ранги
        result = []
        for idx, entry in enumerate(leaderboard, 1):
            result.append({
                "rank": idx,
                "vk_id": entry.get('vk_id'),
                "nickname": entry.get('vk_id'),  # Получить никнейм из users
                "current_value": entry.get('current_value'),
                "card_distribution": entry.get('card_distribution')
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream/leaderboard/{session_id}/ac/top")
async def get_ac_leaderboard(session_id: int, limit: int = Query(10, ge=1, le=50)):
    """Получить лидерборд по AC"""
    try:
        leaderboard = await db.get_ac_leaderboard(session_id, limit)
        return leaderboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream/overlay/card-winner")
async def get_card_winner(session_id: int = Query(None)):
    """Получить последнего победителя в гонке на 10 уровень"""
    try:
        if not session_id:
            session = await db.get_current_active_session()
            if not session:
                raise HTTPException(status_code=404, detail="No active session")
            session_id = session['session_id']
        
        # Получить первого по результатам (rank = 1)
        leaderboard = await db.get_current_leaderboard(session_id, 'card', 1)
        
        if not leaderboard:
            return {"winner_vk_id": None, "winner_nickname": None}
        
        winner = leaderboard[0]
        return {
            "winner_vk_id": winner['vk_id'],
            "winner_nickname": winner['vk_id'],
            "card_type": "N/A",  # Можно расширить JSON в БД
            "card_level": winner['current_value'],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream/overlay/ac-top-5")
async def get_ac_top_5(session_id: int = Query(None)):
    """Получить топ-5 по AC для OBS overlay"""
    try:
        if not session_id:
            session = await db.get_current_active_session()
            if not session:
                raise HTTPException(status_code=404, detail="No active session")
            session_id = session['session_id']
        
        leaderboard = await db.get_ac_leaderboard(session_id, 5)
        return leaderboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream/overlay/rare-drop")
async def get_rare_drop(session_id: int = Query(None)):
    """Получить последний редкий дроп для OBS overlay"""
    try:
        if not session_id:
            session = await db.get_current_active_session()
            if not session:
                return {"drop_id": None}
            session_id = session['session_id']
        
        rare_drops = await db.get_recent_rare_drops(session_id, 1)
        
        if not rare_drops:
            return {"drop_id": None}
        
        drop = rare_drops[0]
        return {
            "vk_id": drop['vk_id'],
            "nickname": drop['nickname'],
            "card_type": drop['card_type'],
            "card_level": drop['card_level'],
            "probability": float(drop['probability']),
            "timestamp": drop['timestamp'],
            "box_type": drop['box_type']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream/sessions/{session_id}/export-csv")
async def export_session_csv(session_id: int):
    """Экспортировать финальные результаты сессии в CSV"""
    try:
        session_info = await db.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Получаем результаты для обоих типов событий (card и ac)
        card_results = await db.get_session_results(session_id, 'card')
        ac_results = await db.get_session_results(session_id, 'ac')
        
        # Формируем CSV
        csv_lines = []
        csv_lines.append(f"VKStream Event Export - {session_info['stream_name']}")
        csv_lines.append(f"Stream Date: {session_info['stream_date']}")
        csv_lines.append(f"Event Type: {session_info['event_type']}")
        csv_lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        csv_lines.append("")
        
        # Card Race Results
        if card_results:
            csv_lines.append("CARD RACE - Level 10 Challenge")
            csv_lines.append("Rank,VK ID,Level")
            for idx, result in enumerate(card_results, 1):
                csv_lines.append(f"{idx},{result['vk_id']},{result['current_value']}")
            csv_lines.append("")
        
        # AC Farming Results
        if ac_results:
            csv_lines.append("AC FARMING")
            csv_lines.append("Rank,VK ID,AC Earned")
            for idx, result in enumerate(ac_results, 1):
                csv_lines.append(f"{idx},{result['vk_id']},{result['ac_earned_this_stream']}")
            csv_lines.append("")
        
        csv_content = "\n".join(csv_lines)
        
        return {
            "filename": f"stream-results-{session_id}.csv",
            "content": csv_content,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream/sessions")
async def get_all_sessions():
    """Получить все завершенные сессии (для архива)"""
    try:
        return await db.get_stream_sessions_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ChatBot Management Endpoints ---

@app.get("/api/chatbot/status")
async def get_chatbot_status():
    """Получить статус чат-бота"""
    return {
        "enabled": CHATBOT_ENABLED,
        "status": "running" if CHATBOT_ENABLED else "disabled",
        "uptime": "N/A"  # Можно добавить отслеживание времени работы
    }

@app.post("/api/chatbot/toggle")
async def toggle_chatbot(enabled: bool = True):
    """Включить/выключить чат-бот"""
    global CHATBOT_ENABLED
    CHATBOT_ENABLED = enabled
    
    if enabled:
        await start_chatbot_background()
    
    return {
        "status": "enabled" if enabled else "disabled",
        "message": "ChatBot " + ("включен" if enabled else "выключен")
    }

@app.get("/api/chatbot/commands")
async def get_chatbot_commands():
    """Получить список команд чат-бота"""
    from chatbot.constants.cnst_Bot import BOT_COMMANDS
    
    # Преобразуем в удобный формат
    commands_list = []
    for category, cmds in BOT_COMMANDS.items():
        commands_list.append({
            "category": category,
            "commands": cmds
        })
    
    return commands_list

# --- WebSocket для real-time обновлений ---

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time обновления для админки"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Обработка сообщений от клиента
            if message.get("type") == "subscribe":
                # Отправляю текущее состояние
                users = await db.get_all_users_admin()
                await websocket.send_json({
                    "type": "initial_data",
                    "users_count": len(users),
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8001, reload=True)
