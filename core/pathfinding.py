"""
Модуль поиска пути A* (A-Star) по тайловой сетке 26x15 с диагоналями
и строгим запретом «срезания углов» между соседними препятствиями.
"""

import math
import heapq
from typing import List, Tuple, Optional, Set, Dict


# Ортогональные и диагональные смещения (dx, dy, cost)
DIRECTIONS = [
    # 4 ортогональных направления (стоимость 1.0)
    (1, 0, 1.0),
    (-1, 0, 1.0),
    (0, 1, 1.0),
    (0, -1, 1.0),
    # 4 диагональных направления (стоимость sqrt(2) ≈ 1.414)
    (1, 1, 1.41421356),
    (1, -1, 1.41421356),
    (-1, 1, 1.41421356),
    (-1, -1, 1.41421356),
]


def octile_heuristic(c1: int, r1: int, c2: int, r2: int) -> float:
    """Эвристика Октиль для 8-направленного движения с диагоналями."""
    dx = abs(c1 - c2)
    dy = abs(r1 - r2)
    return (dx + dy) + (1.41421356 - 2.0) * min(dx, dy)


def find_path(
    game_map,
    start: Tuple[int, int],
    goal: Tuple[int, int]
) -> List[Tuple[int, int]]:
    """
    Рассчитывает кратчайший маршрут A* от start (col, row) до goal (col, row).
    Включает строгий запрет срезания углов между препятствиями/площадками.
    Если целевая точка непроходима, пытается найти ближайшую проходимую соседнюю клетку.
    """
    start_c, start_r = start
    goal_c, goal_r = goal

    if not game_map.is_valid(start_c, start_r):
        return []

    # Если цель не проходима, ищем ближайшую проходимую клетку вокруг цели
    if not game_map.is_walkable(goal_c, goal_r):
        candidates = []
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                nc, nr = goal_c + dc, goal_r + dr
                if game_map.is_walkable(nc, nr):
                    dist = octile_heuristic(nc, nr, start_c, start_r)
                    candidates.append((dist, (nc, nr)))
        if not candidates:
            return []
        candidates.sort()
        goal_c, goal_r = candidates[0][1]

    if (start_c, start_r) == (goal_c, goal_r):
        return [(start_c, start_r)]

    # Приоритетная очередь open_set: (f_score, tie_breaker_counter, (c, r))
    counter = 0
    open_heap = []
    start_h = octile_heuristic(start_c, start_r, goal_c, goal_r)
    heapq.heappush(open_heap, (start_h, counter, (start_c, start_r)))

    came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
    g_score: Dict[Tuple[int, int], float] = {(start_c, start_r): 0.0}
    closed_set: Set[Tuple[int, int]] = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        cur_c, cur_r = current

        if current in closed_set:
            continue
        closed_set.add(current)

        if (cur_c, cur_r) == (goal_c, goal_r):
            # Восстановление маршрута
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        cur_g = g_score[current]

        for dc, dr, move_cost in DIRECTIONS:
            next_c = cur_c + dc
            next_r = cur_r + dr

            if not game_map.is_valid(next_c, next_r):
                continue
            if not game_map.is_walkable(next_c, next_r):
                continue

            # --- СТРОГИЙ ЗАПРЕТ «СРЕЗАНИЯ УГЛОВ» ПРИ ДИАГОНАЛЬНОМ ШАГЕ ---
            # При диагональном смещении ОБЕ смежные ортогональные клетки обязаны быть проходимыми!
            if dc != 0 and dr != 0:
                side_1_walkable = game_map.is_walkable(cur_c + dc, cur_r)
                side_2_walkable = game_map.is_walkable(cur_c, cur_r + dr)
                if not (side_1_walkable and side_2_walkable):
                    # Срезание угла заблокировано: герой не может протиснуться
                    continue

            next_node = (next_c, next_r)
            tentative_g = cur_g + move_cost

            if next_node not in g_score or tentative_g < g_score[next_node]:
                g_score[next_node] = tentative_g
                came_from[next_node] = current
                f_score = tentative_g + octile_heuristic(next_c, next_r, goal_c, goal_r)
                counter += 1
                heapq.heappush(open_heap, (f_score, counter, next_node))

    # Путь не найден
    return []
