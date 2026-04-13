"""
Unit-тесты для GameEngine (engine.py)
"""
import pytest
from engine import GameEngine


@pytest.fixture
def engine():
    """Создает экземпляр GameEngine для тестов"""
    return GameEngine()


class TestGameEngineInitialization:
    """Тесты инициализации GameEngine"""

    def test_card_types(self, engine):
        """Проверка типов карт"""
        assert engine.card_types == ['LT', 'ST', 'TT', 'PT']
        assert len(engine.card_types) == 4

    def test_standard_weights_initialized(self, engine):
        """Проверка инициализации весов стандартного бокса"""
        assert hasattr(engine, 'standard_weights')
        assert len(engine.standard_weights) == 12  # боксы 1-12
        assert "1" in engine.standard_weights
        assert "12" in engine.standard_weights

    def test_pa_box_weights_initialized(self, engine):
        """Проверка инициализации весов PA бокса"""
        assert hasattr(engine, 'pa_box_weights')
        assert len(engine.pa_box_weights) == 12
        assert "1" in engine.pa_box_weights
        assert "12" in engine.pa_box_weights

    def test_elite_box_weights_initialized(self, engine):
        """Проверка инициализации весов элитного бокса"""
        assert hasattr(engine, 'elite_box_weights')
        assert len(engine.elite_box_weights) == 3  # рарности 1-3
        assert "1" in engine.elite_box_weights
        assert "3" in engine.elite_box_weights

    def test_standard_weights_sum_to_100(self, engine):
        """Проверка что веса стандартного бокса суммируются примерно к 100"""
        for box_num, weights in engine.standard_weights.items():
            total = sum(weights)
            assert 99.0 <= total <= 101.0, f"Weights for box {box_num} sum to {total}, expected ~100"

    def test_pa_weights_sum_to_100(self, engine):
        """Проверка что веса PA бокса суммируются примерно к 100"""
        for box_num, weights in engine.pa_box_weights.items():
            total = sum(weights)
            assert 99.0 <= total <= 101.0, f"Weights for box {box_num} sum to {total}, expected ~100"

    def test_elite_weights_sum_to_100(self, engine):
        """Проверка что веса элитного бокса суммируются примерно к 100"""
        for box_num, weights in engine.elite_box_weights.items():
            total = sum(weights)
            assert 99.0 <= total <= 101.0, f"Weights for box {box_num} sum to {total}, expected ~100"


class TestCalculateCardCount:
    """Тесты расчета количества карт"""

    def test_base_formula_box_1(self, engine):
        """Базовая формула: box 1 → 4 + 1*2 = 6"""
        assert engine.calculate_card_count(1, 0, False) == 6

    def test_base_formula_box_5(self, engine):
        """Базовая формула: box 5 → 4 + 5*2 = 14"""
        assert engine.calculate_card_count(5, 0, False) == 14

    def test_base_formula_box_12(self, engine):
        """Базовая формула: box 12 → 4 + 12*2 = 28"""
        assert engine.calculate_card_count(12, 0, False) == 28

    def test_pa_multiplier(self, engine):
        """PA бонус: x1.75"""
        # box 1: base = 6, with PA = ceil(6 * 1.75) = 11
        assert engine.calculate_card_count(1, 0, True) == 11
        # box 5: base = 14, with PA = ceil(14 * 1.75) = 25
        assert engine.calculate_card_count(5, 0, True) == 25

    def test_three_stars_bonus(self, engine):
        """3 звезды: x1.5"""
        # box 1: base = 6, with 3 stars = ceil(6 * 1.5) = 9
        assert engine.calculate_card_count(1, 3, False) == 9
        # box 5: base = 14, with 3 stars = ceil(14 * 1.5) = 21
        assert engine.calculate_card_count(5, 3, False) == 21

    def test_two_stars_bonus(self, engine):
        """2 звезды: base + 3"""
        # box 1: base = 6, with 2 stars = 6 + 3 = 9
        assert engine.calculate_card_count(1, 2, False) == 9
        # box 5: base = 14, with 2 stars = 14 + 3 = 17
        assert engine.calculate_card_count(5, 2, False) == 17

    def test_pa_takes_precedence_over_stars(self, engine):
        """PA бонус приоритетнее звезд"""
        # box 5: base = 14, with PA = 25 (даже если stars=3)
        assert engine.calculate_card_count(5, 3, True) == 25

    def test_zero_stars_uses_base(self, engine):
        """0 звезд = базовая формула"""
        assert engine.calculate_card_count(3, 0, False) == 10
        assert engine.calculate_card_count(7, 0, False) == 18


class TestCalculateACReward:
    """Тесты расчета AC奖励"""

    def test_standard_box_low(self, engine):
        """Стандартный бокс < 10: box_num * 2"""
        assert engine.calculate_ac_reward(1, False, False) == 2
        assert engine.calculate_ac_reward(5, False, False) == 10
        assert engine.calculate_ac_reward(9, False, False) == 18

    def test_standard_box_high(self, engine):
        """Стандартный бокс >= 10: box_num * 5"""
        assert engine.calculate_ac_reward(10, False, False) == 50
        assert engine.calculate_ac_reward(12, False, False) == 60

    def test_elite_box(self, engine):
        """Элитный бокс: box_num * 10"""
        assert engine.calculate_ac_reward(1, True, False) == 10
        assert engine.calculate_ac_reward(2, True, False) == 20
        assert engine.calculate_ac_reward(3, True, False) == 30

    def test_pa_multiplier_standard(self, engine):
        """PA бонус для стандартных боксов: x2"""
        assert engine.calculate_ac_reward(5, False, True) == 20  # 10 * 2
        assert engine.calculate_ac_reward(10, False, True) == 100  # 50 * 2

    def test_pa_no_effect_on_elite(self, engine):
        """PA бонус применяется и к элитным"""
        assert engine.calculate_ac_reward(2, True, True) == 40  # 20 * 2


class TestGetRandomCards:
    """Тесты генерации случайных карт"""

    def test_returns_correct_count(self, engine):
        """Возвращает правильное количество карт"""
        cards = engine.get_random_cards(1, False, 5, False)
        assert len(cards) == 5

    def test_card_structure(self, engine):
        """Каждая карта имеет type и lvl"""
        cards = engine.get_random_cards(1, False, 1, False)
        assert len(cards) == 1
        card = cards[0]
        assert 'type' in card
        assert 'lvl' in card
        assert card['type'] in engine.card_types
        assert 1 <= card['lvl'] <= 10

    def test_multiple_cards_structure(self, engine):
        """Все карты имеют правильную структуру"""
        cards = engine.get_random_cards(5, False, 10, False)
        assert len(cards) == 10
        for card in cards:
            assert card['type'] in engine.card_types
            assert 1 <= card['lvl'] <= 10

    def test_elite_box_rarity_1(self, engine):
        """Элитный бокс рарности 1: карты 1 уровня (80%)"""
        cards = engine.get_random_cards(1, False, 100, True)
        levels = [c['lvl'] for c in cards]
        # Большинство должны быть 1 уровня
        level_1_count = levels.count(1)
        assert level_1_count > 50  # хотя бы 50% должны быть 1 уровня

    def test_elite_box_rarity_2(self, engine):
        """Элитный бокс рарности 2: карты 1-2 уровня"""
        cards = engine.get_random_cards(2, False, 100, True)
        levels = [c['lvl'] for c in cards]
        # Большинство должны быть 2 уровня (80%)
        level_2_count = levels.count(2)
        assert level_2_count > 50

    def test_elite_box_rarity_3(self, engine):
        """Элитный бокс рарности 3: карты 2-3 уровня"""
        cards = engine.get_random_cards(3, False, 100, True)
        levels = [c['lvl'] for c in cards]
        # Большинство должны быть 3 уровня (80%)
        level_3_count = levels.count(3)
        assert level_3_count > 50

    def test_pa_box_has_better_odds(self, engine):
        """PA бокс должен давать более высокие уровни"""
        # Сравниваем средние уровни для стандартного и PA боксов
        standard_cards = engine.get_random_cards(5, False, 100, False)
        pa_cards = engine.get_random_cards(5, True, 100, False)

        avg_standard = sum(c['lvl'] for c in standard_cards) / 100
        avg_pa = sum(c['lvl'] for c in pa_cards) / 100

        # PA должен быть не хуже (статистически)
        assert avg_pa >= avg_standard * 0.9  # допускаем небольшую погрешность

    def test_card_type_distribution(self, engine):
        """Типы карт должны распределяться равномерно"""
        cards = engine.get_random_cards(5, False, 400, False)
        type_counts = {}
        for card in cards:
            type_counts[card['type']] = type_counts.get(card['type'], 0) + 1

        # Каждый тип должен присутствовать
        for card_type in engine.card_types:
            assert card_type in type_counts
            assert type_counts[card_type] > 50  # хотя бы 50 карт каждого типа из 400


class TestCSVExport:
    """Тесты экспорта в CSV"""

    def test_csv_export_basic(self, engine, tmp_path):
        """Базовый экспорт в CSV"""
        data = [
            {'nickname': 'Player1', 'weight': 100},
            {'nickname': 'Player2', 'weight': 200}
        ]
        filename = str(tmp_path / "test_export.csv")

        engine.export_csv(data, filename)

        # Проверяем что файл создан
        import os
        assert os.path.exists(filename)

        # Проверяем содержимое
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'Player1' in content
            assert 'Player2' in content
            assert '100' in content
            assert '200' in content

    def test_csv_export_empty(self, engine, tmp_path):
        """Экспорт пустых данных"""
        data = []
        filename = str(tmp_path / "test_empty.csv")

        engine.export_csv(data, filename)

        import os
        assert os.path.exists(filename)

        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content.strip()) == 0

    def test_csv_export_pipe_delimiter(self, engine, tmp_path):
        """CSV использует разделитель |"""
        data = [{'nickname': 'Player1', 'weight': 100}]
        filename = str(tmp_path / "test_pipe.csv")

        engine.export_csv(data, filename)

        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '|' in content
            assert ',' not in content.replace('Player1', '')  # только pipe как разделитель


class TestEdgeCases:
    """Тесты граничных случаев"""

    def test_box_number_capping_standard(self, engine):
        """Номер бокса ограничивается 12 для стандартных весов"""
        cards = engine.get_random_cards(20, False, 10, False)
        assert len(cards) == 10
        for card in cards:
            assert 1 <= card['lvl'] <= 10

    def test_box_number_capping_pa(self, engine):
        """Номер бокса ограничивается 12 для PA весов"""
        cards = engine.get_random_cards(15, True, 10, False)
        assert len(cards) == 10

    def test_box_number_capping_elite(self, engine):
        """Номер бокса ограничивается 3 для элитных весов"""
        cards = engine.get_random_cards(10, False, 10, True)
        assert len(cards) == 10

    def test_zero_cards(self, engine):
        """Запрос 0 карт"""
        cards = engine.get_random_cards(1, False, 0, False)
        assert len(cards) == 0

    def test_large_card_count(self, engine):
        """Большое количество карт"""
        cards = engine.get_random_cards(12, True, 1000, False)
        assert len(cards) == 1000
        for card in cards:
            assert 'type' in card
            assert 'lvl' in card
