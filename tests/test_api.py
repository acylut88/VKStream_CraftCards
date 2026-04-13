"""
Integration-тесты для API (api.py)
Используем pytest и httpx для тестирования FastAPI endpoints
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from api import app
from database import DatabaseManager
import os
import sys

# Подменяем БД для тестов
TEST_DB_PATH = "test_stream_game_api.db"


@pytest_asyncio.fixture
async def setup_test_db():
    """Создает и очищает тестовую БД"""
    db = DatabaseManager(TEST_DB_PATH)
    await db.init_db()
    yield db
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest_asyncio.fixture
async def client(setup_test_db):
    """Создает тестовый HTTP клиент с тестовой БД"""
    # Подменяем db в api.py и main.py на тестовый
    import api
    import main
    api.db = setup_test_db
    main.db = setup_test_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestUserEndpoints:
    """Тесты endpoints для пользователей"""

    async def test_get_users_empty(self, client):
        """GET /api/users - пустой список"""
        response = await client.get("/api/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_create_user(self, client):
        """POST /api/users - создание пользователя"""
        response = await client.post(
            "/api/users",
            json={
                "vk_id": "test_user_1",
                "nickname": "TestPlayer",
                "stars": 5,
                "pa_charges": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['vk_id'] == "test_user_1"
        assert data['nickname'] == "TestPlayer"
        assert data['stars'] == 5

    async def test_create_user_duplicate(self, client):
        """POST /api/users - дубликат"""
        await client.post(
            "/api/users",
            json={"vk_id": "dup_user", "nickname": "DupPlayer"}
        )
        response = await client.post(
            "/api/users",
            json={"vk_id": "dup_user", "nickname": "DupPlayer2"}
        )
        assert response.status_code == 400

    async def test_get_user(self, client):
        """GET /api/users/{vk_id} - получение пользователя"""
        await client.post(
            "/api/users",
            json={"vk_id": "get_user", "nickname": "GetPlayer"}
        )
        response = await client.get("/api/users/get_user")
        assert response.status_code == 200
        data = response.json()
        assert data['vk_id'] == "get_user"
        assert data['nickname'] == "GetPlayer"

    async def test_get_user_not_found(self, client):
        """GET /api/users/{vk_id} - не найден"""
        response = await client.get("/api/users/nonexistent")
        assert response.status_code == 404

    async def test_update_user(self, client):
        """POST /api/users/{vk_id}/update - обновление"""
        await client.post(
            "/api/users",
            json={"vk_id": "update_user", "nickname": "OldName", "stars": 3}
        )
        response = await client.post(
            "/api/users/update_user/update",
            json={"nickname": "NewName", "stars": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'updated'

        # Проверяем что изменения сохранились
        response = await client.get("/api/users/update_user")
        assert response.status_code == 200
        data = response.json()
        assert data['nickname'] == "NewName"
        assert data['stars'] == 5

    async def test_delete_user(self, client):
        """DELETE /api/users/{vk_id} - удаление"""
        await client.post(
            "/api/users",
            json={"vk_id": "delete_user", "nickname": "DeletePlayer"}
        )
        response = await client.delete("/api/users/delete_user")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'deleted'

        # Проверяем что удален
        response = await client.get("/api/users/delete_user")
        assert response.status_code == 404


class TestBoxEndpoints:
    """Тесты endpoints для боксов"""

    async def test_give_boxes_standard(self, client):
        """POST /api/users/{vk_id}/boxes - стандартные боксы"""
        await client.post(
            "/api/users",
            json={"vk_id": "box_user", "nickname": "BoxPlayer"}
        )
        response = await client.post(
            "/api/users/box_user/boxes",
            json={"vk_id": "box_user", "count": 2, "rarity": 0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['boxes_added'] == 2
        assert 'results' in data

    async def test_give_boxes_elite(self, client):
        """POST /api/users/{vk_id}/boxes - элитные боксы"""
        await client.post(
            "/api/users",
            json={"vk_id": "elite_user", "nickname": "ElitePlayer"}
        )
        response = await client.post(
            "/api/users/elite_user/boxes",
            json={"vk_id": "elite_user", "count": 1, "rarity": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['boxes_added'] == 1

    async def test_give_boxes_creates_user(self, client):
        """POST /api/users/{vk_id}/boxes - создает пользователя если нет"""
        response = await client.post(
            "/api/users/new_user/boxes",
            json={"vk_id": "new_user", "nickname": "NewPlayer", "count": 1, "rarity": 0}
        )
        assert response.status_code == 200

        # Проверяем что пользователь создан
        response = await client.get("/api/users/new_user")
        assert response.status_code == 200

    async def test_get_user_inventory(self, client):
        """GET /api/users/{vk_id}/inventory - получение инвентаря"""
        await client.post(
            "/api/users",
            json={"vk_id": "inv_user", "nickname": "InvPlayer"}
        )
        await client.post(
            "/api/users/inv_user/boxes",
            json={"vk_id": "inv_user", "count": 1, "rarity": 0}
        )

        response = await client.get("/api/users/inv_user/inventory")
        assert response.status_code == 200
        data = response.json()
        assert data['vk_id'] == "inv_user"
        assert 'cards' in data


class TestAnalyticsEndpoints:
    """Тесты endpoints для аналитики"""

    async def test_get_analytics_empty(self, client):
        """GET /api/analytics - пустая аналитика"""
        response = await client.get("/api/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data['total_users'] == 0
        assert data['total_boxes'] == 0
        assert data['total_ac'] == 0

    async def test_get_analytics_with_data(self, client):
        """GET /api/analytics - с данными"""
        await client.post(
            "/api/users",
            json={"vk_id": "analytics_user", "nickname": "AnalyticsPlayer"}
        )
        await client.post(
            "/api/users/analytics_user/boxes",
            json={"vk_id": "analytics_user", "count": 1, "rarity": 0}
        )

        response = await client.get("/api/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data['total_users'] == 1
        assert data['active_users'] >= 1
        assert data['total_boxes'] >= 1
        assert 'top_players' in data
        assert 'logs_count' in data

    async def test_get_logs(self, client):
        """GET /api/logs - получение логов"""
        await client.post(
            "/api/users",
            json={"vk_id": "log_user", "nickname": "LogPlayer"}
        )
        await client.post(
            "/api/users/log_user/boxes",
            json={"vk_id": "log_user", "count": 1, "rarity": 0}
        )

        response = await client.get("/api/logs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Проверяем структуру лога
        log = data[0]
        assert 'timestamp' in log
        assert 'nickname' in log
        assert 'box_type' in log
        assert 'count' in log

    async def test_get_timeline(self, client):
        """GET /api/stats/timeline - временная шкала"""
        response = await client.get("/api/stats/timeline")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestStreamEndpoints:
    """Тесты endpoints для стримов"""

    async def test_start_stream_day(self, client):
        """POST /api/stream/start-day"""
        response = await client.post("/api/stream/start-day")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'

    async def test_create_stream_session(self, client):
        """POST /api/stream/session/create"""
        response = await client.post(
            "/api/stream/session/create",
            json={
                "event_type": "both",
                "stream_date": "2026-04-13",
                "stream_name": "Test Stream"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert 'session_id' in data
        assert data['event_type'] == 'both'
        assert data['status'] == 'active'

    async def test_finish_stream_session(self, client):
        """POST /api/stream/session/{id}/finish"""
        # Создаем сессию
        response = await client.post(
            "/api/stream/session/create",
            json={"event_type": "card"}
        )
        session_id = response.json()['session_id']

        # Завершаем
        response = await client.post(f"/api/stream/session/{session_id}/finish")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['session_id'] == session_id

    async def test_get_ac_leaderboard(self, client):
        """GET /api/stream/leaderboard/{id}/ac/top"""
        response = await client.post(
            "/api/stream/session/create",
            json={"event_type": "ac_farming"}
        )
        session_id = response.json()['session_id']

        response = await client.get(f"/api/stream/leaderboard/{session_id}/ac/top")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_rare_drop(self, client):
        """GET /api/stream/overlay/rare-drop"""
        response = await client.post(
            "/api/stream/session/create",
            json={"event_type": "card"}
        )
        session_id = response.json()['session_id']

        response = await client.get(f"/api/stream/overlay/rare-drop")
        assert response.status_code == 200

    async def test_export_session_csv(self, client):
        """GET /api/stream/sessions/{id}/export-csv"""
        response = await client.post(
            "/api/stream/session/create",
            json={"event_type": "both", "stream_name": "Test Stream"}
        )
        session_id = response.json()['session_id']

        response = await client.get(f"/api/stream/sessions/{session_id}/export-csv")
        assert response.status_code == 200
        data = response.json()
        assert 'filename' in data
        assert 'content' in data
        assert '.csv' in data['filename']


class TestDangerousEndpoints:
    """Тесты опасных endpoints"""

    async def test_clear_all_data(self, client):
        """POST /api/stream/clear-all"""
        await client.post(
            "/api/users",
            json={"vk_id": "clear_user", "nickname": "ClearPlayer"}
        )
        response = await client.post("/api/stream/clear-all")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'database_cleared'

        # Проверяем что все очищено
        response = await client.get("/api/users")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    async def test_finish_stream(self, client):
        """POST /api/stream/finish"""
        response = await client.post("/api/stream/finish")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'stream_finished'


class TestGetAllSessions:
    """Тесты получения всех сессий"""

    async def test_get_all_sessions_empty(self, client):
        """GET /api/stream/sessions - пустой список"""
        response = await client.get("/api/stream/sessions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_get_all_sessions_with_data(self, client):
        """GET /api/stream/sessions - с данными"""
        await client.post(
            "/api/stream/session/create",
            json={"event_type": "card", "stream_name": "Session 1"}
        )
        await client.post(
            "/api/stream/session/create",
            json={"event_type": "ac_farming", "stream_name": "Session 2"}
        )

        response = await client.get("/api/stream/sessions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
