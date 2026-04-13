"""
Unit-тесты для DatabaseManager (database.py)
"""
import pytest
import pytest_asyncio
import os
import aiosqlite
from database import DatabaseManager


@pytest.fixture
def db_path(tmp_path):
    """Создает временный путь к БД"""
    return str(tmp_path / "test_stream_game.db")


@pytest_asyncio.fixture
async def db(db_path):
    """Создает и инициализирует тестовую БД"""
    database = DatabaseManager(db_path)
    await database.init_db()
    yield database
    # Cleanup после теста
    if os.path.exists(db_path):
        os.remove(db_path)


class TestDatabaseInitialization:
    """Тесты инициализации БД"""

    async def test_init_db_creates_tables(self, db, db_path):
        """Проверка что init_db создает все таблицы"""
        async with aiosqlite.connect(db_path) as conn:
            async with conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ) as cursor:
                tables = await cursor.fetchall()
                table_names = [t[0] for t in tables]

        expected_tables = [
            'inventory', 'logs', 'stream_event_results',
            'stream_rare_drops', 'stream_session_snapshots',
            'stream_sessions', 'users'
        ]
        for table in expected_tables:
            assert table in table_names

    async def test_init_db_idempotent(self, db):
        """init_db можно вызывать повторно без ошибок"""
        await db.init_db()  # Не должно вызвать исключение
        await db.init_db()
        await db.init_db()


class TestUserOperations:
    """Тесты операций с пользователями"""

    async def test_get_user_creates_new(self, db):
        """get_user создает нового пользователя если не существует"""
        user = await db.get_user("test_vk_id", "TestPlayer")
        assert user is not None
        assert user['vk_id'] == "test_vk_id"
        assert user['nickname'] == "TestPlayer"

    async def test_get_user_existing(self, db):
        """get_user возвращает существующего пользователя"""
        await db.get_user("test_vk_id", "TestPlayer")
        user = await db.get_user("test_vk_id")
        assert user is not None
        assert user['vk_id'] == "test_vk_id"

    async def test_get_user_without_nickname_raises(self, db):
        """get_user без nickname для несуществующего пользователя возвращает None"""
        user = await db.get_user("nonexistent_id")
        assert user is None

    async def test_new_user_default_values(self, db):
        """Новый пользователь получает дефолтные значения"""
        user = await db.get_user("test_vk_id", "TestPlayer")
        assert user['stars'] == 3
        assert user['pa_charges'] == 2
        assert user['pa_active_today'] == 0
        assert user['std_boxes_today'] == 0
        assert user['elite_boxes_today'] == 0
        assert user['ac_balance'] == 0
        assert user['ac_today'] == 0

    async def test_create_user(self, db):
        """Создание пользователя через create_user"""
        user = await db.create_user("new_user", "NewPlayer", stars=5, pa_charges=3)
        assert user is not None
        assert user['vk_id'] == "new_user"
        assert user['nickname'] == "NewPlayer"
        assert user['stars'] == 5
        assert user['pa_charges'] == 3

    async def test_create_user_duplicate_raises(self, db):
        """Создание дубликата пользователя вызывает ошибку"""
        await db.create_user("dup_user", "DupPlayer")
        with pytest.raises(ValueError, match="already exists"):
            await db.create_user("dup_user", "DupPlayer2")

    async def test_rename_user(self, db):
        """Смена никнейма пользователя"""
        await db.create_user("rename_user", "OldName")
        await db.rename_user("rename_user", "NewName")
        user = await db.get_user("rename_user")
        assert user['nickname'] == "NewName"

    async def test_update_user_field_increment(self, db):
        """Инкремент поля пользователя"""
        await db.create_user("update_user", "UpdatePlayer", stars=3)
        await db.update_user_field("update_user", "stars", 2)
        user = await db.get_user("update_user")
        assert user['stars'] == 5

    async def test_update_user_field_decrement(self, db):
        """Декремент поля пользователя"""
        await db.create_user("update_user", "UpdatePlayer", stars=5)
        await db.update_user_field("update_user", "stars", -2)
        user = await db.get_user("update_user")
        assert user['stars'] == 3

    async def test_update_user_field_reset(self, db):
        """Сброс поля пользователя"""
        await db.create_user("update_user", "UpdatePlayer", stars=5)
        await db.update_user_field("update_user", "stars", action="reset")
        user = await db.get_user("update_user")
        assert user['stars'] == 0

    async def test_update_user_field_invalid_field(self, db):
        """Обновление недопустимого поля ничего не делает"""
        await db.create_user("update_user", "UpdatePlayer")
        await db.update_user_field("update_user", "invalid_field", 10)
        # Исключение не должно вызываться, просто ничего не произойдет

    async def test_update_user_field_min_zero(self, db):
        """Поле не может стать меньше 0"""
        await db.create_user("update_user", "UpdatePlayer", stars=2)
        await db.update_user_field("update_user", "stars", -10)
        user = await db.get_user("update_user")
        assert user['stars'] == 0

    async def test_delete_user_completely(self, db):
        """Полное удаление пользователя"""
        await db.create_user("delete_user", "DeletePlayer")
        await db.delete_user_completely("delete_user")
        user = await db.get_user("delete_user")
        assert user is None

    async def test_get_all_users_admin(self, db):
        """Получение всех пользователей"""
        await db.create_user("user1", "Player1")
        await db.create_user("user2", "Player2")
        await db.create_user("user3", "Player3")

        users = await db.get_all_users_admin()
        assert len(users) == 3


class TestACOperations:
    """Тесты операций с AC"""

    async def test_update_ac_increase(self, db):
        """Увеличение AC"""
        await db.create_user("ac_user", "ACPlayer")
        await db.update_ac("ac_user", 100)
        user = await db.get_user("ac_user")
        assert user['ac_balance'] == 100
        assert user['ac_today'] == 100

    async def test_update_ac_multiple(self, db):
        """Несколько увеличений AC"""
        await db.create_user("ac_user", "ACPlayer")
        await db.update_ac("ac_user", 50)
        await db.update_ac("ac_user", 30)
        user = await db.get_user("ac_user")
        assert user['ac_balance'] == 80
        assert user['ac_today'] == 80

    async def test_update_ac_negative_does_not_go_below_zero(self, db):
        """AC не может быть меньше 0"""
        await db.create_user("ac_user", "ACPlayer")
        await db.update_ac("ac_user", 10)
        await db.update_ac("ac_user", -20)
        user = await db.get_user("ac_user")
        assert user['ac_balance'] == 0
        assert user['ac_today'] == 0


class TestInventoryOperations:
    """Тесты операций с инвентарем"""

    async def test_add_raw_cards(self, db):
        """Добавление карт в инвентарь"""
        await db.create_user("inv_user", "InvPlayer")
        cards = [
            {'type': 'LT', 'lvl': 1},
            {'type': 'ST', 'lvl': 2},
            {'type': 'LT', 'lvl': 1}
        ]
        await db.add_raw_cards("inv_user", cards)

        inventories = await db.get_all_inventories_grouped()
        assert "inv_user" in inventories
        user_cards = inventories["inv_user"]

        # LT lvl 1 должно быть 2 штуки
        lt_cards = [c for c in user_cards if c['card_type'] == 'LT' and c['card_level'] == 1]
        assert len(lt_cards) == 1
        assert lt_cards[0]['quantity'] == 2

    async def test_add_raw_cards_increment(self, db):
        """Добавление карт увеличивает количество"""
        await db.create_user("inv_user", "InvPlayer")
        cards1 = [{'type': 'LT', 'lvl': 1}]
        await db.add_raw_cards("inv_user", cards1)

        cards2 = [{'type': 'LT', 'lvl': 1}]
        await db.add_raw_cards("inv_user", cards2)

        inventories = await db.get_all_inventories_grouped()
        lt_cards = [c for c in inventories["inv_user"] if c['card_type'] == 'LT' and c['card_level'] == 1]
        assert lt_cards[0]['quantity'] == 2

    async def test_perform_auto_merge_basic(self, db):
        """Базовый тест авто-мержа 2-в-1"""
        await db.create_user("merge_user", "MergePlayer")

        # Добавляем 2 карты LT lvl 1
        cards = [{'type': 'LT', 'lvl': 1}, {'type': 'LT', 'lvl': 1}]
        await db.add_raw_cards("merge_user", cards)

        # Выполняем мерж
        merges = await db.perform_auto_merge("merge_user")

        # Должен произойти один мерж
        assert len(merges) == 1
        assert merges[0]['type'] == 'LT'
        assert merges[0]['to_lvl'] == 2
        assert merges[0]['count'] == 1

        # Проверяем инвентарь
        inventories = await db.get_all_inventories_grouped()
        user_cards = inventories["merge_user"]

        # LT lvl 1 должно остаться 0
        lt_1 = [c for c in user_cards if c['card_type'] == 'LT' and c['card_level'] == 1]
        assert len(lt_1) == 0 or lt_1[0]['quantity'] == 0

        # LT lvl 2 должно быть 1
        lt_2 = [c for c in user_cards if c['card_type'] == 'LT' and c['card_level'] == 2]
        assert len(lt_2) == 1
        assert lt_2[0]['quantity'] == 1

    async def test_perform_auto_merge_multiple(self, db):
        """Мерж нескольких пар - каскадный"""
        await db.create_user("merge_user", "MergePlayer")

        # Добавляем 4 карты LT lvl 1 (2 пары)
        cards = [
            {'type': 'LT', 'lvl': 1},
            {'type': 'LT', 'lvl': 1},
            {'type': 'LT', 'lvl': 1},
            {'type': 'LT', 'lvl': 1}
        ]
        await db.add_raw_cards("merge_user", cards)

        merges = await db.perform_auto_merge("merge_user")

        # Каскадный мерж: 4x lvl 1 → 2x lvl 2 → 1x lvl 3
        # Должно быть 2-3 мержа в зависимости от каскада
        assert len(merges) >= 1
        # Общее количество созданных карт lvl 2+ должно быть правильным
        inventories = await db.get_all_inventories_grouped()
        user_cards = inventories["merge_user"]
        # Проверяем что в итоге есть карта lvl 3
        lt_3 = [c for c in user_cards if c['card_type'] == 'LT' and c['card_level'] == 3]
        assert len(lt_3) == 1
        assert lt_3[0]['quantity'] == 1

    async def test_perform_auto_merge_with_remainder(self, db):
        """Мерж с остатком"""
        await db.create_user("merge_user", "MergePlayer")

        # Добавляем 3 карты LT lvl 1 (1 пара + 1 остаток)
        cards = [
            {'type': 'LT', 'lvl': 1},
            {'type': 'LT', 'lvl': 1},
            {'type': 'LT', 'lvl': 1}
        ]
        await db.add_raw_cards("merge_user", cards)

        merges = await db.perform_auto_merge("merge_user")

        assert len(merges) == 1
        assert merges[0]['count'] == 1

        # Должна остаться 1 карта lvl 1
        inventories = await db.get_all_inventories_grouped()
        user_cards = inventories["merge_user"]
        lt_1 = [c for c in user_cards if c['card_type'] == 'LT' and c['card_level'] == 1]
        assert lt_1[0]['quantity'] == 1

    async def test_clear_user_inventory(self, db):
        """Очистка инвентаря пользователя"""
        await db.create_user("inv_user", "InvPlayer")
        cards = [{'type': 'LT', 'lvl': 1}, {'type': 'ST', 'lvl': 2}]
        await db.add_raw_cards("inv_user", cards)

        await db.clear_user_inventory("inv_user")

        inventories = await db.get_all_inventories_grouped()
        assert "inv_user" not in inventories or len(inventories["inv_user"]) == 0

    async def test_clear_all_inventories(self, db):
        """Очистка всех инвентарей"""
        await db.create_user("user1", "Player1")
        await db.create_user("user2", "Player2")
        await db.add_raw_cards("user1", [{'type': 'LT', 'lvl': 1}])
        await db.add_raw_cards("user2", [{'type': 'ST', 'lvl': 1}])

        await db.clear_all_inventories()

        inventories = await db.get_all_inventories_grouped()
        assert len(inventories) == 0

    async def test_get_all_weights(self, db):
        """Расчет веса инвентаря"""
        await db.create_user("weight_user", "WeightPlayer")

        # Добавляем: 1x lvl 1 (weight=1), 1x lvl 2 (weight=2), 1x lvl 3 (weight=4)
        cards = [
            {'type': 'LT', 'lvl': 1},
            {'type': 'LT', 'lvl': 2},
            {'type': 'LT', 'lvl': 3}
        ]
        await db.add_raw_cards("weight_user", cards)

        weights = await db.get_all_weights()
        assert len(weights) == 1
        assert weights[0]['nickname'] == "WeightPlayer"
        assert weights[0]['weight'] == 7  # 1 + 2 + 4


class TestBoxCounters:
    """Тесты счетчиков боксов"""

    async def test_increment_standard_box(self, db):
        """Инкремент стандартного бокса"""
        await db.create_user("box_user", "BoxPlayer")
        await db.increment_box_counter("box_user", is_elite=False)

        user = await db.get_user("box_user")
        assert user['std_boxes_today'] == 1
        assert user['elite_boxes_today'] == 0

    async def test_increment_elite_box(self, db):
        """Инкремент элитного бокса"""
        await db.create_user("box_user", "BoxPlayer")
        await db.increment_box_counter("box_user", is_elite=True)

        user = await db.get_user("box_user")
        assert user['std_boxes_today'] == 0
        assert user['elite_boxes_today'] == 1

    async def test_increment_pa_charge_consumed(self, db):
        """Инкремент бокса списывает PA заряд если он есть"""
        await db.create_user("box_user", "BoxPlayer", pa_charges=1)
        await db.increment_box_counter("box_user", is_elite=False)

        user = await db.get_user("box_user")
        assert user['pa_charges'] == 0
        assert user['pa_active_today'] == 1


class TestDayReset:
    """Тесты сброса дня"""

    async def test_reset_day_counters(self, db):
        """Сброс дневных счетчиков"""
        await db.create_user("reset_user", "ResetPlayer")
        await db.increment_box_counter("reset_user", is_elite=False)
        await db.increment_box_counter("reset_user", is_elite=True)

        await db.reset_day()

        user = await db.get_user("reset_user")
        assert user['std_boxes_today'] == 0
        assert user['elite_boxes_today'] == 0
        assert user['pa_active_today'] == 0
        assert user['ac_today'] == 0

    async def test_reset_day_stars_decrement(self, db):
        """Сброс дня уменьшает звезды если боксов < 12"""
        await db.create_user("reset_user", "ResetPlayer", stars=5)
        await db.reset_day()

        user = await db.get_user("reset_user")
        assert user['stars'] == 4  # Уменьшилось на 1

    async def test_reset_day_stars_min_1(self, db):
        """Звезды не могут упасть ниже 1"""
        await db.create_user("reset_user", "ResetPlayer", stars=1)
        await db.reset_day()

        user = await db.get_user("reset_user")
        assert user['stars'] == 1


class TestLogs:
    """Тесты логирования"""

    async def test_add_log(self, db):
        """Добавление лога"""
        await db.add_log(
            nickname="TestPlayer",
            box_type="Стандарт",
            count=10,
            rare_drops=["LT-5", "ST-4"],
            merges=["LT-6"],
            is_elite=False,
            ac_won=50
        )

        logs = await db.get_recent_logs()
        assert len(logs) == 1
        assert logs[0]['nickname'] == "TestPlayer"
        assert logs[0]['box_type'] == "Стандарт"
        assert logs[0]['count'] == 10
        assert "LT-5" in logs[0]['rare_drops']
        assert logs[0]['ac_won'] == 50

    async def test_add_log_elite(self, db):
        """Добавление лога для элитного бокса"""
        await db.add_log(
            nickname="ElitePlayer",
            box_type="Элитный",
            count=5,
            rare_drops=["TT-3"],
            merges=[],
            is_elite=True,
            ac_won=100
        )

        logs = await db.get_recent_logs()
        assert len(logs) == 1
        assert logs[0]['is_elite'] == 1


class TestClearOperations:
    """Тесты полной очистки"""

    async def test_clear_full_database(self, db):
        """Полная очистка БД"""
        await db.create_user("user1", "Player1")
        await db.create_user("user2", "Player2")
        await db.add_raw_cards("user1", [{'type': 'LT', 'lvl': 1}])

        await db.clear_full_database()

        users = await db.get_all_users_admin()
        assert len(users) == 0

        inventories = await db.get_all_inventories_grouped()
        assert len(inventories) == 0
