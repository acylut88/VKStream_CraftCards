"""
Расширенное REST API для админ-панели React
"""
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import json

from database import DatabaseManager
from main import db, engine, process_lootbox_opening, game_logs

app = FastAPI(title="VKStream API", version="1.0")

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
    vk_id: str
    nickname: str
    stars: int
    pa_charges: int
    pa_active_today: int
    std_boxes_today: int
    elite_boxes_today: int
    ac_balance: int
    ac_today: int

    class Config:
        from_attributes = True

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

class LogResponse(BaseModel):
    timestamp: str
    nickname: str
    box_type: str
    count: int
    rare_drops: str
    merges: str
    ac_won: int

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
    return users

@app.get("/api/users/{vk_id}", response_model=UserResponse)
async def get_user(vk_id: str):
    """Информация конкретного пользователя"""
    user = await db.get_user(vk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

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
    return logs

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
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)
