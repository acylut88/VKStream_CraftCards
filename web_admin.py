from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager # Добавили это
import uvicorn

from database import DatabaseManager
from main import finish_stream_logic, process_lootbox_opening, game_logs
    


# Новый способ инициализации БД (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Действия при старте
    await db.init_db()
    # Подгружаем старые логи
    recent = await db.get_recent_logs(100)
    game_logs.extend(recent)
    yield
    # Действия при выключении (если нужны)

app = FastAPI(lifespan=lifespan)
db = DatabaseManager()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def admin_index(request: Request):
    users = await db.get_all_users_admin()
    inventories = await db.get_all_inventories_grouped() # Получаем все карты
    
    return templates.TemplateResponse(
        request=request, 
        name="admin.html", 
        context={
            "users": users,
            "inventories": inventories # Передаем в шаблон
        }
    )



@app.post("/test-drop")
async def test_drop(vk_id: str = Form(...), nickname: str = Form(...)):
    # Вызываем нашу асинхронную логику
    await process_lootbox_opening(vk_id, nickname)
    return RedirectResponse(url="/", status_code=303)

@app.post("/finish-stream")
async def finish_stream():
    await finish_stream_logic()
    return RedirectResponse(url="/", status_code=303)

# Добавь это в web_admin.py

@app.post("/test-elite-drop")
async def test_elite_drop(vk_id: str = Form(...), nickname: str = Form(...)):
    """Кнопка ручного начисления элитного бокса"""
    await process_lootbox_opening(vk_id, nickname, is_elite=True)
    return RedirectResponse(url="/", status_code=303)

@app.post("/update-user")
async def update_user(
    vk_id: str = Form(...), 
    field: str = Form(...), 
    action: str = Form(...)
):
    """Метод для кнопок +/- в админке"""
    change = 1 if action == 'inc' else -1
    
    # Вызываем метод менеджера БД, а не пишем SQL здесь
    await db.update_user_field(vk_id, field, change)
    
    return RedirectResponse(url="/", status_code=303)



@app.get("/logs", response_class=HTMLResponse)
async def view_logs(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={"logs": game_logs}
    )

@app.post("/clear-all-inventories")
async def clear_all():
    await db.clear_all_inventories()
    return RedirectResponse(url="/", status_code=303)

@app.post("/clear-user-inventory")
async def clear_user(vk_id: str = Form(...)):
    await db.clear_user_inventory(vk_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/clear-full-database")
async def clear_full():
    await db.clear_full_database()
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete-user")
async def delete_user(vk_id: str = Form(...)):
    await db.delete_user_completely(vk_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/rename-user")
async def rename(vk_id: str = Form(...), new_nickname: str = Form(...)):
    await db.rename_user(vk_id, new_nickname)
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_admin:app", host="127.0.0.1", port=8000, reload=True)
