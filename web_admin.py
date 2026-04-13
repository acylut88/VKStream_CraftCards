import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

# Импортируем наши модули
from database import DatabaseManager
from main import db, engine, process_lootbox_opening, finish_stream_logic, export_raffle, game_logs

# 1. LIFESPAN - Инициализация при старте
@asynccontextmanager
async def lifespan(app: FastAPI):
    # А. Создаем таблицы, если их нет
    await db.init_db()
    
    # Б. Подгружаем последние 100 логов из БД в кэш (main.game_logs)
    recent_logs = await db.get_recent_logs(100)
    game_logs.clear()
    # Разворачиваем список, чтобы новые были вверху, если это не сделано в SQL
    game_logs.extend(recent_logs)
    
    print(f"Система запущена. Подгружено логов: {len(game_logs)}")
    yield
    # Действия при выключении (если нужны)

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# --- РОУТЫ АДМИНКИ ---

@app.get("/", response_class=HTMLResponse)
async def admin_index(request: Request):
    users = await db.get_all_users_admin()
    inventories = await db.get_all_inventories_grouped()
    return templates.TemplateResponse(
        request=request, 
        name="admin.html", 
        context={
            "users": users, 
            "inventories": inventories,
            "game_logs": game_logs # Передаем логи для отображения, если нужно на главной
        }
    )

@app.get("/logs", response_class=HTMLResponse)
async def view_logs(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={"logs": game_logs}
    )

# --- ЭКСПОРТ И СБРОС ---

@app.post("/export/{mode}")
async def export_data(mode: str):
    """Экспорт AC или WEIGHT в CSV"""
    filename = await export_raffle(mode)
    return FileResponse(filename, filename=filename)

@app.post("/finish-stream")
async def finish():
    """Сброс дня через логику из main.py"""
    await finish_stream_logic()
    return RedirectResponse(url="/", status_code=303)

# --- УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ---

@app.post("/update-user")
async def update_user(vk_id: str = Form(...), field: str = Form(...), action: str = Form(...)):
    change = 1 if action == 'inc' else -1
    await db.update_user_field(vk_id, field, change)
    return RedirectResponse(url="/", status_code=303)

@app.post("/admin-update-ac")
async def admin_update_ac(vk_id: str = Form(...), amount: int = Form(...)):
    """Ручное изменение баланса AC"""
    await db.update_ac(vk_id, amount)
    return RedirectResponse(url="/", status_code=303)

@app.post("/rename-user")
async def rename(vk_id: str = Form(...), new_nickname: str = Form(...)):
    await db.rename_user(vk_id, new_nickname)
    return RedirectResponse(url="/", status_code=303)

# --- ОТКРЫТИЕ БОКСОВ ---

@app.post("/test-drop")
async def test_drop(vk_id: str = Form(...), nickname: str = Form(...)):
    await process_lootbox_opening(vk_id, nickname, is_elite=False)
    return RedirectResponse(url="/", status_code=303)

@app.post("/test-elite-drop")
async def test_elite_drop(vk_id: str = Form(...), nickname: str = Form(...)):
    await process_lootbox_opening(vk_id, nickname, is_elite=True)
    return RedirectResponse(url="/", status_code=303)

# --- ОЧИСТКА ---

@app.post("/delete-user")
async def delete_user(vk_id: str = Form(...)):
    await db.delete_user_completely(vk_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/clear-user-inventory")
async def clear_inv(vk_id: str = Form(...)):
    await db.clear_user_inventory(vk_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/clear-all-inventories")
async def clear_all_inv():
    await db.clear_all_inventories()
    return RedirectResponse(url="/", status_code=303)

@app.post("/clear-full-database")
async def clear_all_db():
    await db.clear_full_database()
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run("web_admin:app", host="127.0.0.1", port=8000, reload=True)