import random
import math
import statistics
import csv

from engine import GameEngine

class GameSimulation:
    def __init__(self):
        # Создаем экземпляр движка один раз
        self.engine = GameEngine()
        # Теперь все веса доступны через self.engine.standard_weights и т.д.
        self.card_types = self.engine.card_types

    def add_and_merge(self, inv, cards):
        for c_type, lvl in cards:
            inv[c_type][lvl] += 1
            for l in range(1, 10):
                if inv[c_type][l] >= 2:
                    new_cards = inv[c_type][l] // 2
                    inv[c_type][l+1] += new_cards
                    inv[c_type][l] %= 2

    def open_box(self, b_num, stars, has_pa, is_elite):
        # Используем твой боевой метод расчета количества, чтобы формулы всегда совпадали!
        count = self.engine.calculate_card_count(b_num, stars, has_pa)
        
        # Выбираем веса прямо из engine
        key = str(min(b_num, 12))
        if is_elite:
            weights = self.engine.elite_box_weights[str(min(b_num, 3))]
        elif has_pa:
            weights = self.engine.pa_box_weights[key]
        else:
            weights = self.engine.standard_weights[key]
            
        dropped = []
        for _ in range(count):
            lvl = random.choices(range(1, 11), weights=weights, k=1)[0]
            c_type = random.choice(self.card_types)
            dropped.append((c_type, lvl))
        return dropped

    def run_single_test(self, has_pa, use_elite, target_lvl_10_count, target_types_count):
        inventory = {t: {l: 0 for l in range(1, 11)} for t in self.card_types}
        total_boxes, days = 0, 0
        
        while True:
            days += 1
            # Стандартный цикл (12 боксов)
            for b_num in range(1, 13):
                total_boxes += 1
                cards = self.open_box(b_num, 3, has_pa, False)
                self.add_and_merge(inventory, cards)
                if self.check_win(inventory, target_lvl_10_count, target_types_count):
                    return days, total_boxes
            # Элитный цикл (3 бокса)
            if use_elite:
                for b_num in range(1, 4):
                    total_boxes += 1
                    cards = self.open_box(b_num, 3, has_pa, True)
                    self.add_and_merge(inventory, cards)
                    if self.check_win(inventory, target_lvl_10_count, target_types_count):
                        return days, total_boxes

    def check_win(self, inv, needed_10s, needed_types):
        """
        Проверяет, сколько типов карт достигли нужного количества карт 10 уровня.
        Пример: needed_10s=4, needed_types=1 -> Нужно 4 карты 10лвл одного любого типа.
        Пример: needed_10s=1, needed_types=4 -> Нужно собрать по 1 карте 10лвл во всех 4 типах.
        """
        types_met_condition = 0
        for t in self.card_types:
            if inv[t][10] >= needed_10s:
                types_met_condition += 1
        
        return types_met_condition >= needed_types

def start_full_test(has_pa, use_elite, target_10s, target_types, iterations):
    """
    Точка запуска теста.
    target_10s: сколько карт 10 лвл должно быть в одном типе
    target_types: в скольких типах должно выполниться условие (1-4)
    """

    sim = GameSimulation()
    days_list = []
    boxes_list = []

    for _ in range(iterations):
        d, b = sim.run_single_test(has_pa, use_elite, target_10s, target_types)
        days_list.append(d)
        boxes_list.append(b)

    avg_d = statistics.mean(days_list)
    avg_b = statistics.mean(boxes_list)

    print(f"\n--- Результаты теста ({iterations} циклов) ---")
    print(f"Условия: ПА={has_pa}, Элита={use_elite}, Цель: {target_10s} шт. 10лвл в {target_types} типах")
    print(f"Среднее время: {avg_d:.1f} дн.")
    print(f"Среднее кол-во боксов: {avg_b:.1f} шт.")
    
    # Сохранение в CSV
    with open('custom_test_results.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='|')
        writer.writerow([has_pa, use_elite, target_10s, target_types, iterations, avg_d, avg_b])

# --- ПРИМЕРЫ ЗАПУСКА ---

# 1. 10 итераций: С ПА и Элитой, собрать по одной 10-ке в 4 разных типах
# start_full_test(has_pa=True, use_elite=True, target_10s=1, target_types=4, iterations=100)

# 2. 10 итераций: Без ПА, собрать 4 карты 10-го уровня в рамках ОДНОГО типа
start_full_test(has_pa=True, use_elite=False, target_10s=1, target_types=1, iterations=100)
