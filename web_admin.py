from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager # Добавили это
import uvicorn

from database import DatabaseManager
from main import finish_stream_logic, process_lootbox_opening

# Новый способ инициализации БД (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Действия при старте
    await db.init_db()
    yield
    # Действия при выключении (если нужны)

app = FastAPI(lifespan=lifespan)
db = DatabaseManager()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def admin_index(request: Request):
    users = await db.get_all_users_admin()
    return templates.TemplateResponse(
        request=request, 
        name="admin.html", 
        context={"users": users}
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_admin:app", host="127.0.0.1", port=8000, reload=True)
