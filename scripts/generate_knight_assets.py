"""
Генератор ручного пиксель-арта для Рыцаря-командира (уровень Tiny Swords / Blasphemous / классических RPG):
- Строго попиксельные матрицы без pygame.draw.circle/ellipse и мягких градиентов
- Чёткий тёмный 1px-контур #141013
- Hue-shifting: тёплый золотой свет -> холодная сине-стальная тень; винно-фиолетовая тень плаща -> алый -> оранжево-алый блик
- Грозный закрытый топфхельм с Т-образной прорезью и длинным развевающимся плюмажем
- Ребристые золотые наплечники, выраженная узкая талия, стройные поножи, боковой гербовый щит и широкий меч
"""

import os
from typing import Dict, List, Tuple
import pygame

OUT_DIR = os.path.join("assets", "heroes", "knight")

# Чёткий тёмный контур #141013
OUTLINE = (20, 16, 19, 255)

PALETTE: Dict[str, Tuple[int, int, int, int]] = {
    ".": (0, 0, 0, 0),
    "O": OUTLINE,

    # Сталь с hue-shifting (холодная индиго-стальная тень -> светлый тёпло-серебристый блик)
    "a": (52, 58, 84, 255),      # глубокая холодная тень стали
    "b": (88, 98, 128, 255),     # тень стали
    "c": (138, 152, 182, 255),   # базовый металл
    "d": (192, 206, 228, 255),   # светлый металл
    "e": (244, 244, 232, 255),   # тёплый слоново-белый блик клинка/доспеха

    # Королевское золото с hue-shifting (тёплая умбра -> сияющий золотой блик)
    "k": (108, 60, 22, 255),     # тёмная тень ребра золота
    "g": (158, 98, 28, 255),     # тень золота
    "G": (214, 148, 38, 255),    # база золота
    "y": (248, 204, 70, 255),    # яркое золото
    "Y": (255, 246, 168, 255),   # золотой блик

    # Алый плащ и плюмаж (3+ тона складок с hue-shifting)
    "r": (82, 18, 36, 255),      # глубокая винная тень складки
    "R": (146, 26, 40, 255),     # основная тень плаща
    "p": (204, 46, 48, 255),     # яркий алый
    "P": (242, 92, 62, 255),     # тёплый ало-оранжевый блик

    # Кожа (ремень, перчатки, сапоги)
    "l": (52, 30, 24, 255),      # тёмная кожа
    "L": (92, 54, 36, 255),      # средняя кожа
    "t": (136, 86, 52, 255),     # светлая кожа

    # Т-образная прорезь забрала
    "v": (16, 12, 16, 255),      # глубокая темнота прорези

    # Поле гербового щита (тёмно-сапфировое с золотым узором)
    "n": (32, 42, 82, 255),
    "N": (52, 72, 128, 255),

    # Золото-белый пиксельный след рубящего удара клинка (без размытия)
    "w": (255, 252, 240, 255),   # чистый белый край слэша
    "q": (255, 224, 110, 220),   # золотой пиксельный след
    "Q": (232, 152, 44, 155),    # янтарный хвост дуги

    # Пиксельная тень под ногами (никаких ellipse!)
    "s": (20, 16, 19, 115),
    "S": (20, 16, 19, 60),
}


def _new_grid(w: int = 32, h: int = 32) -> List[List[str]]:
    return [["." for _ in range(w)] for _ in range(h)]


def _plot(grid: List[List[str]], x: int, y: int, ch: str) -> None:
    if 0 <= x < len(grid[0]) and 0 <= y < len(grid):
        grid[y][x] = ch


def _draw_rows(grid: List[List[str]], rows: List[Tuple[int, int, str]]) -> None:
    for y, x0, text in rows:
        for i, ch in enumerate(text):
            if ch != " ":
                _plot(grid, x0 + i, y, ch)


def _apply_outline(grid: List[List[str]]) -> None:
    """Строит чёткий 1px тёмный контур #141013 вокруг непрозрачных пикселей тела."""
    h, w = len(grid), len(grid[0])
    non_body = (".", "O", "s", "S", "w", "q", "Q")
    outline_pts: List[Tuple[int, int]] = []
    for y in range(h):
        for x in range(w):
            if grid[y][x] in (".", "s", "S"):
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] not in non_body:
                        outline_pts.append((x, y))
                        break
    for x, y in outline_pts:
        grid[y][x] = "O"


def _render_grid(grid: List[List[str]]) -> pygame.Surface:
    h, w = len(grid), len(grid[0])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w):
            ch = grid[y][x]
            if ch != ".":
                surf.set_at((x, y), PALETTE[ch])
    return surf


def _draw_pixel_shadow(grid: List[List[str]], cx: int = 16, y: int = 29) -> None:
    """Строгая пиксельная полоса тени под ногами (без circle/ellipse)."""
    _draw_rows(grid, [
        (y,     cx - 5, "SsssssssssS"),
        (y + 1, cx - 4, "SsssssssS"),
    ])


def _draw_cape(grid: List[List[str]], wave: int, lean_x: int = 0, dy: int = 0) -> None:
    """Длинный алый плащ за спиной с 3 оттенками складок."""
    y0 = 12 + dy
    x0 = 4 + lean_x
    if wave == 0:
        rows = [
            (y0 + 0, x0 + 5, "pPRr"),
            (y0 + 1, x0 + 4, "pPPRRr"),
            (y0 + 2, x0 + 3, "pPRpRRr"),
            (y0 + 3, x0 + 3, "RRpPRRr"),
            (y0 + 4, x0 + 2, "rRpPRRrr"),
            (y0 + 5, x0 + 2, "rRpPRRrr"),
            (y0 + 6, x0 + 2, "rRRpRRrr"),
            (y0 + 7, x0 + 1, "rrRpRRrr"),
            (y0 + 8, x0 + 1, "rrRpRRr"),
            (y0 + 9, x0 + 2, "rrRRrr"),
            (y0 + 10, x0 + 2, "rrrRr"),
        ]
    elif wave == 1:
        rows = [
            (y0 + 0, x0 + 4, "pPRRr"),
            (y0 + 1, x0 + 3, "pPPRRr"),
            (y0 + 2, x0 + 2, "pPRpRRr"),
            (y0 + 3, x0 + 1, "pRRpPRRr"),
            (y0 + 4, x0 + 1, "RRpPRRRr"),
            (y0 + 5, x0 + 0, "rRpPRRRrr"),
            (y0 + 6, x0 + 0, "rRRpRRrr"),
            (y0 + 7, x0 + 1, "rrRpRRrr"),
            (y0 + 8, x0 + 1, "rrRRRr"),
            (y0 + 9, x0 + 2, "rrrRrr"),
        ]
    elif wave == 2:
        # Сильный взмах плаща назад при быстром шаге/атаке
        rows = [
            (y0 + 0, x0 + 3, "pPPRr"),
            (y0 + 1, x0 + 1, "PpPRRRr"),
            (y0 + 2, x0 + 0, "pPRpPRRRr"),
            (y0 + 3, x0 - 1, "rRpPRRRRr"),
            (y0 + 4, x0 - 2, "rRRpPRRRrr"),
            (y0 + 5, x0 - 2, "rrRpPRRRrr"),
            (y0 + 6, x0 - 1, "rrrRRRr"),
            (y0 + 7, x0 + 0, "rrrrRr"),
        ]
    else:
        rows = [
            (y0 + 0, x0 + 5, "pPRr"),
            (y0 + 1, x0 + 4, "pPRRRr"),
            (y0 + 2, x0 + 4, "RRpRRr"),
            (y0 + 3, x0 + 3, "rRpPRRr"),
            (y0 + 4, x0 + 3, "rRpPRRrr"),
            (y0 + 5, x0 + 3, "rRRpRRrr"),
            (y0 + 6, x0 + 2, "rrRpRRrr"),
            (y0 + 7, x0 + 2, "rrRpRRr"),
            (y0 + 8, x0 + 3, "rrRRrr"),
            (y0 + 9, x0 + 3, "rrrRr"),
        ]
    _draw_rows(grid, rows)


def _draw_legs(grid: List[List[str]], pose: str, cx: int = 16, dy: int = 0) -> None:
    """Стройные латные поножи и сапоги, чётко разделённые при шаге."""
    y0 = 21 + dy
    x = cx - 4
    if pose == "stand":
        rows = [
            (y0 + 0, x,     "dcca  dcca"),
            (y0 + 1, x,     "dcba  dcba"),
            (y0 + 2, x,     "yGba  yGba"),
            (y0 + 3, x,     "dcba  dcba"),
            (y0 + 4, x,     "tLLl  tLLl"),
            (y0 + 5, x,     "LLll  LLll"),
            (y0 + 6, x,     "tLLll tLLll"),
            (y0 + 7, x,     "lllll lllll"),
        ]
    elif pose == "run1":
        # Широкий шаг вперёд правой ногой, левая отведена назад
        rows = [
            (y0 + 0, x - 1, "dcca   dcca"),
            (y0 + 1, x - 2, "dcba    dcba"),
            (y0 + 2, x - 2, "yGba     yGba"),
            (y0 + 3, x - 3, "tLLl      dcba"),
            (y0 + 4, x - 3, "LLll      tLLl"),
            (y0 + 5, x - 4, "lllll     LLll"),
            (y0 + 6, x + 6, "tLLll"),
            (y0 + 7, x + 6, "lllll"),
        ]
    elif pose == "run2":
        rows = [
            (y0 + 0, x,     "dcca  dcca"),
            (y0 + 1, x - 1, "dcba   dcba"),
            (y0 + 2, x - 1, "yGba    yGba"),
            (y0 + 3, x - 2, "tLLl     dcba"),
            (y0 + 4, x - 2, "LLll     tLLl"),
            (y0 + 5, x - 2, "llll     tLLll"),
            (y0 + 6, x + 6, "lllll"),
        ]
    elif pass_r_pose := (pose == "pass1"):
        # Опорная левая нога чётко стоит на тени (y+7), правая поднята в проносе
        rows = [
            (y0 + 0, x + 1, "dccaa dca"),
            (y0 + 1, x + 1, "dcbba dba"),
            (y0 + 2, x + 1, "yGbba yGa"),
            (y0 + 3, x + 1, "dcbba tLl"),
            (y0 + 4, x + 1, "tLLl  Lll"),
            (y0 + 5, x + 1, "LLll"),
            (y0 + 6, x + 1, "tLLll"),
            (y0 + 7, x + 1, "lllll"),
        ]
    elif pose == "run3":
        # Широкий шаг левой ногой вперёд
        rows = [
            (y0 + 0, x - 1, "dcca   dcca"),
            (y0 + 1, x - 1, "dcba    dcba"),
            (y0 + 2, x - 2, "yGba     yGba"),
            (y0 + 3, x - 2, "dcba      tLLl"),
            (y0 + 4, x - 2, "tLLl      LLll"),
            (y0 + 5, x - 2, "LLll      llll"),
            (y0 + 6, x - 2, "tLLll"),
            (y0 + 7, x - 2, "lllll"),
        ]
    elif pose == "run4":
        rows = [
            (y0 + 0, x,     "dcca  dcca"),
            (y0 + 1, x,     "dcba   dcba"),
            (y0 + 2, x - 1, "yGba    yGba"),
            (y0 + 3, x - 1, "dcba     tLLl"),
            (y0 + 4, x - 1, "tLLl     LLll"),
            (y0 + 5, x - 1, "LLll     llll"),
            (y0 + 6, x - 1, "tLLll"),
            (y0 + 7, x - 1, "lllll"),
        ]
    elif pose == "pass2":
        # Опорная правая нога чётко на земле (y+7), левая переносится вперёд
        rows = [
            (y0 + 0, x + 1, "dca dccaa"),
            (y0 + 1, x + 1, "dba dcbba"),
            (y0 + 2, x + 1, "yGa yGbba"),
            (y0 + 3, x + 1, "tLl dcbba"),
            (y0 + 4, x + 1, "Lll tLLl"),
            (y0 + 5, x + 5, "LLll"),
            (y0 + 6, x + 5, "tLLll"),
            (y0 + 7, x + 5, "lllll"),
        ]
    elif pose == "lunge":
        # Мощный боевой выпад
        rows = [
            (y0 + 0, x - 1, "dcca    dcca"),
            (y0 + 1, x - 2, "dcba     dcba"),
            (y0 + 2, x - 3, "yGba      yGba"),
            (y0 + 3, x - 3, "dcba      dcba"),
            (y0 + 4, x - 4, "tLLl       tLLl"),
            (y0 + 5, x - 4, "LLll       LLll"),
            (y0 + 6, x - 4, "tLLll      tLLll"),
            (y0 + 7, x - 4, "lllll      lllll"),
        ]
    else:
        rows = []
    _draw_rows(grid, rows)


def _draw_torso_and_pauldrons(grid: List[List[str]], cx: int = 16, dy: int = 0, shoulder_dy: int = 0) -> None:
    """Мощные ребристые золотые наплечники, стальная кираса и узкая талия с ремнём."""
    y0 = 11 + dy
    x = cx - 6
    # Ребристые золотые наплечники (с тёплыми бликами Y/y и глубокими рёбрами k/g)
    pauldrons = [
        (y0 + 0 + shoulder_dy, x + 0, "yYYy      yYYy"),
        (y0 + 1 + shoulder_dy, x - 1, "YyyGg    gGyYY"),
        (y0 + 2 + shoulder_dy, x - 1, "GkkGG    GGkkG"),
        (y0 + 3 + shoulder_dy, x + 0, "yyGGg    gGGyy"),
        (y0 + 4 + shoulder_dy, x + 0, "gGk        kGg"),
    ]
    _draw_rows(grid, pauldrons)

    # Стальная кираса с золотой V-окантовкой, узкая талия и коричневый ремень с пряжкой
    cuirass = [
        (y0 + 1, x + 3, "yGddddGy"),
        (y0 + 2, x + 3, "edddccba"),
        (y0 + 3, x + 3, "eddccbba"),
        (y0 + 4, x + 3, "dcccbba"),
        (y0 + 5, x + 4, "yGGyGG"),       # золотая окантовка талии
        (y0 + 6, x + 4, "tLyYyL"),       # узкая талия: кожаный ремень + золотая пряжка
        (y0 + 7, x + 4, "LlGygL"),
        (y0 + 8, x + 3, "pPRyGRRp"),     # алые тассеты (боевая юбка)
        (y0 + 9, x + 3, "RRr  rRR"),
    ]
    _draw_rows(grid, cuirass)


def _draw_topfhelm_and_plume(
    grid: List[List[str]], cx: int = 16, dy: int = 0, plume_wave: int = 0
) -> None:
    """Грозный закрытый топфхельм с Т-образной прорезью и длинным развевающимся алым плюмажем."""
    hy = 2 + dy
    px = cx - 4

    # 1. Длинный развевающийся алый плюмаж назад (влево)
    if plume_wave == 0:
        plume = [
            (hy - 1, px - 1, "pPPp"),
            (hy + 0, px - 4, "PppPpp"),
            (hy + 1, px - 6, "RpPRRp"),
            (hy + 2, px - 6, "rRRp"),
            (hy + 3, px - 5, "rr"),
        ]
    elif plume_wave == 1:
        plume = [
            (hy - 1, px - 2, "pPPpp"),
            (hy + 0, px - 5, "pPPppp"),
            (hy + 1, px - 7, "pRRpRR"),
            (hy + 2, px - 7, "rRRR"),
            (hy + 3, px - 5, "rr"),
        ]
    else:
        plume = [
            (hy + 0, px - 2, "pPPpp"),
            (hy + 1, px - 6, "PpPRRpp"),
            (hy + 2, px - 8, "pRRRp"),
            (hy + 3, px - 7, "rrr"),
        ]
    _draw_rows(grid, plume)

    # 2. Компактный угловатый закрытый топфхельм (никаких круглых шариков!)
    hx = cx - 4
    helm = [
        (hy + 0, hx + 1, "edddcb"),      # плоский/рубленый верх топфхельма
        (hy + 1, hx + 0, "eedddccba"),   # грань шлема
        (hy + 2, hx + 0, "yYyyyyyGG"),   # золотой обруч короны
        (hy + 3, hx + 0, "dOvvvvvvOa"),  # горизонтальная прорезь Т-забрала
        (hy + 4, hx + 0, "dcvvOvvvca"),  # вертикальная переносица + Т-щель
        (hy + 5, hx + 0, "dcOvOvvOba"),  # прорезь и дыхательные щели
        (hy + 6, hx + 0, "dcOvOvCOba"),
        (hy + 7, hx + 0, "dcceOyccba"),  # стальная перекладина + золотая вертикаль
        (hy + 8, hx + 1, "dcccbba"),     # острый подбородок шлема
    ]
    # Исправляем случайный 'C' -> 'c'
    helm = [(y, x0, txt.replace("C", "c")) for (y, x0, txt) in helm]
    _draw_rows(grid, helm)


def _draw_side_shield(grid: List[List[str]], sx: int, sy: int) -> None:
    """Вытянутый гербовый щит сбоку (не закрывает торс!) с золотым узором и стальной каймой."""
    shield = [
        (sy + 0, sx,     "dcccba"),
        (sy + 1, sx,     "dNyyNa"),
        (sy + 2, sx,     "cNyyNb"),
        (sy + 3, sx,     "cyYYyb"),
        (sy + 4, sx,     "cNyyNb"),
        (sy + 5, sx + 1, "bNyn"),
        (sy + 6, sx + 1, "bnGb"),
        (sy + 7, sx + 2, "ca"),
    ]
    _draw_rows(grid, shield)


def _draw_sword(grid: List[List[str]], pose: str, cx: int = 16, dy: int = 0) -> None:
    """Блестящий широкий рыцарский меч с золотой гардой и долом по центру клинка."""
    if pose == "ready":
        rows = [
            (5 + dy,  cx + 11, "e"),
            (6 + dy,  cx + 10, "ee"),
            (7 + dy,  cx + 9,  "edb"),
            (8 + dy,  cx + 9,  "edc"),
            (9 + dy,  cx + 8,  "edbc"),
            (10 + dy, cx + 7,  "edbc"),
            (11 + dy, cx + 7,  "edc"),
            (12 + dy, cx + 6,  "edbc"),
            (13 + dy, cx + 6,  "dcb"),
            (14 + dy, cx + 5,  "yGY"),   # золотая гарда
            (15 + dy, cx + 4,  "dcl"),   # перчатка + рукоять
            (16 + dy, cx + 4,  "y"),     # золотое навершие
        ]
    elif pose == "run_fwd":
        rows = [
            (8 + dy,  cx + 13, "e"),
            (9 + dy,  cx + 12, "ee"),
            (10 + dy, cx + 11, "edb"),
            (11 + dy, cx + 10, "edbc"),
            (12 + dy, cx + 9,  "edbc"),
            (13 + dy, cx + 8,  "edbc"),
            (14 + dy, cx + 7,  "dcb"),
            (15 + dy, cx + 6,  "yGY"),
            (16 + dy, cx + 5,  "dcl"),
            (17 + dy, cx + 4,  "y"),
        ]
    elif pose == "run_back":
        rows = [
            (5 + dy,  cx + 8, "e"),
            (6 + dy,  cx + 7, "ee"),
            (7 + dy,  cx + 7, "edb"),
            (8 + dy,  cx + 6, "edbc"),
            (9 + dy,  cx + 6, "edbc"),
            (10 + dy, cx + 5, "edbc"),
            (11 + dy, cx + 5, "dcb"),
            (12 + dy, cx + 5, "dcb"),
            (13 + dy, cx + 4, "yGY"),
            (14 + dy, cx + 4, "dc"),
        ]
    elif pose == "windup":
        # Высокий замах над головой с разворотом плеча
        rows = [
            (0 + dy,  cx + 10, "e"),
            (1 + dy,  cx + 9,  "ee"),
            (2 + dy,  cx + 9,  "edb"),
            (3 + dy,  cx + 8,  "edbc"),
            (4 + dy,  cx + 8,  "edbc"),
            (5 + dy,  cx + 7,  "edbc"),
            (6 + dy,  cx + 7,  "edc"),
            (7 + dy,  cx + 6,  "dcb"),
            (8 + dy,  cx + 5,  "yGY"),
            (9 + dy,  cx + 5,  "dcl"),
            (10 + dy, cx + 5,  "y"),
        ]
    elif pose == "strike":
        # Мощный широкий горизонтальный рубящий выпад вперёд
        rows = [
            (14 + dy, cx + 5, "dc"),
            (15 + dy, cx + 6, "yGY"),
            (15 + dy, cx + 8, "eedddccde"),
            (16 + dy, cx + 7, "ddccccdce"),
            (16 + dy, cx + 16, "e"),
        ]
    elif pose == "follow":
        # Завершение удара вниз-вперёд
        rows = [
            (15 + dy, cx + 5, "dc"),
            (16 + dy, cx + 6, "yGY"),
            (17 + dy, cx + 7, "edc"),
            (18 + dy, cx + 8, "edc"),
            (19 + dy, cx + 9, "edc"),
            (20 + dy, cx + 10, "ed"),
            (21 + dy, cx + 11, "e"),
        ]
    else:
        rows = []
    _draw_rows(grid, rows)


def _add_slash_arc(grid: List[List[str]], phase: int) -> None:
    """Чёткая белая/золотая пиксельная дуга следа клинка (никаких градиентов/размытий)."""
    if phase == 1:
        # Быстрая рубящая дуга сверху-справа к лезвию
        arc = [
            (4,  18, "QQ"),
            (5,  20, "Qqq"),
            (6,  22, "Qqqw"),
            (7,  23, "Qqqww"),
            (8,  24, "Qqqww"),
            (9,  25, "Qqqww"),
            (10, 25, "Qqqww"),
            (11, 25, "Qqqww"),
            (12, 25, "Qqqww"),
            (13, 24, "Qqqww"),
            (14, 24, "Qqqw"),
            (15, 25, "qqw"),
        ]
    else:
        # Остаточные золотые искры и шлейф после проноса
        arc = [
            (11, 26, "Q"),
            (12, 26, "Qq"),
            (13, 27, "Qq"),
            (14, 26, "Qqq"),
            (15, 26, "Qqq"),
            (16, 25, "Qqq"),
            (17, 25, "Qq"),
            (18, 26, "Qq"),
            (19, 27, "Q"),
            (8,  24, "q"),
        ]
    _draw_rows(grid, arc)


def _compose_knight_frame(
    cx: int = 16,
    dy: int = 0,
    shoulder_dy: int = 0,
    plume_wave: int = 0,
    cape_wave: int = 0,
    leg_pose: str = "stand",
    shield_dx: int = 0,
    shield_dy: int = 0,
    sword_pose: str = "ready",
    slash_phase: int = 0,
) -> pygame.Surface:
    g = _new_grid(32, 32)
    _draw_pixel_shadow(g, cx=cx, y=29)
    _draw_cape(g, wave=cape_wave, lean_x=(cx - 16), dy=dy)
    _draw_legs(g, pose=leg_pose, cx=cx, dy=dy)
    _draw_torso_and_pauldrons(g, cx=cx, dy=dy, shoulder_dy=shoulder_dy)
    _draw_topfhelm_and_plume(g, cx=cx, dy=dy, plume_wave=plume_wave)
    _draw_sword(g, pose=sword_pose, cx=cx, dy=dy)
    _draw_side_shield(g, sx=(cx - 10 + shield_dx), sy=(13 + dy + shield_dy))
    _apply_outline(g)
    if slash_phase > 0:
        _add_slash_arc(g, slash_phase)
    return _render_grid(g)


def generate_knight_sheets() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. knight_idle.png (4 кадра 32x32): лёгкое дыхание плеч/шлема + волна по плащу и плюмажу
    idle_cfgs = [
        {"dy": 0, "shoulder_dy": 0, "plume_wave": 0, "cape_wave": 0, "shield_dy": 0},
        {"dy": 0, "shoulder_dy": 1, "plume_wave": 1, "cape_wave": 1, "shield_dy": 1},
        {"dy": 1, "shoulder_dy": 0, "plume_wave": 2, "cape_wave": 1, "shield_dy": 1},
        {"dy": 0, "shoulder_dy": 0, "plume_wave": 1, "cape_wave": 3, "shield_dy": 0},
    ]
    idle_sheet = pygame.Surface((32 * 4, 32), pygame.SRCALPHA)
    for i, cfg in enumerate(idle_cfgs):
        idle_sheet.blit(_compose_knight_frame(cx=16, leg_pose="stand", sword_pose="ready", **cfg), (i * 32, 0))
    pygame.image.save(idle_sheet, os.path.join(OUT_DIR, "knight_idle.png"))

    # 2. knight_walk.png (6 кадров 32x32): динамичный бег/шаг с наклоном корпуса вперёд, взмахом плаща и движением ног
    walk_cfgs = [
        {"cx": 17, "dy": 0,  "shoulder_dy": 0, "plume_wave": 1, "cape_wave": 2, "leg_pose": "run1",  "shield_dx": 1,  "shield_dy": 0, "sword_pose": "run_back"},
        {"cx": 17, "dy": 1,  "shoulder_dy": 0, "plume_wave": 2, "cape_wave": 2, "leg_pose": "run2",  "shield_dx": 0,  "shield_dy": 1, "sword_pose": "ready"},
        {"cx": 17, "dy": 0,  "shoulder_dy": 0, "plume_wave": 1, "cape_wave": 1, "leg_pose": "pass1", "shield_dx": -1, "shield_dy": 0, "sword_pose": "run_fwd"},
        {"cx": 17, "dy": 0,  "shoulder_dy": 0, "plume_wave": 2, "cape_wave": 2, "leg_pose": "run3",  "shield_dx": -1, "shield_dy": 0, "sword_pose": "run_fwd"},
        {"cx": 17, "dy": 1,  "shoulder_dy": 0, "plume_wave": 1, "cape_wave": 2, "leg_pose": "run4",  "shield_dx": 0,  "shield_dy": 1, "sword_pose": "ready"},
        {"cx": 17, "dy": 0,  "shoulder_dy": 0, "plume_wave": 0, "cape_wave": 1, "leg_pose": "pass2", "shield_dx": 1,  "shield_dy": 0, "sword_pose": "run_back"},
    ]
    walk_sheet = pygame.Surface((32 * 6, 32), pygame.SRCALPHA)
    for i, cfg in enumerate(walk_cfgs):
        walk_sheet.blit(_compose_knight_frame(**cfg), (i * 32, 0))
    pygame.image.save(walk_sheet, os.path.join(OUT_DIR, "knight_walk.png"))

    # 3. knight_attack.png (4 кадра 32x32): замах над головой -> рубящий удар со следом -> доводка -> возврат в стойку
    atk_cfgs = [
        {"cx": 15, "dy": 0,  "shoulder_dy": -1, "plume_wave": 0, "cape_wave": 3, "leg_pose": "stand", "shield_dx": -1, "shield_dy": -1, "sword_pose": "windup", "slash_phase": 0},
        {"cx": 17, "dy": 1,  "shoulder_dy": 0,  "plume_wave": 2, "cape_wave": 2, "leg_pose": "lunge", "shield_dx": 1,  "shield_dy": 0,  "sword_pose": "strike", "slash_phase": 1},
        {"cx": 17, "dy": 1,  "shoulder_dy": 0,  "plume_wave": 1, "cape_wave": 1, "leg_pose": "lunge", "shield_dx": 0,  "shield_dy": 0,  "sword_pose": "follow", "slash_phase": 2},
        {"cx": 16, "dy": 0,  "shoulder_dy": 0,  "plume_wave": 0, "cape_wave": 0, "leg_pose": "stand", "shield_dx": 0,  "shield_dy": 0,  "sword_pose": "ready",  "slash_phase": 0},
    ]
    atk_sheet = pygame.Surface((32 * 4, 32), pygame.SRCALPHA)
    for i, cfg in enumerate(atk_cfgs):
        atk_sheet.blit(_compose_knight_frame(**cfg), (i * 32, 0))
    pygame.image.save(atk_sheet, os.path.join(OUT_DIR, "knight_attack.png"))


def generate_portrait() -> None:
    """Попиксельный портрет Рыцаря-командира 32x32 в топфхельме с золотыми наплечниками."""
    os.makedirs(OUT_DIR, exist_ok=True)
    g = _new_grid(32, 32)
    rows = [
        # Развевающийся алый плюмаж
        (2,  10, "pPPpp"),
        (3,  8,  "PpPRpp"),
        (4,  7,  "rRPRp"),
        (5,  7,  "rrRp"),
        # Топфхельм с золотой короной и Т-прорезью
        (4,  12, "edddccba"),
        (5,  11, "eeddddccba"),
        (6,  11, "yYyyyyyyGG"),
        (7,  11, "dcOvvvvvvOa"),
        (8,  11, "dcOvvOvvvca"),
        (9,  11, "dcOvOOvvOba"),
        (10, 11, "dcOvOOvvOba"),
        (11, 11, "dcceOycccba"),
        (12, 12, "dcccccbba"),
        # Мощные ребристые золотые наплечники, стальная кираса и алый плащ (ровный силуэт)
        (13, 8,  "pPRyYYyddddyYYyRp"),
        (14, 6,  "pPPRYyyGddddGyyYRpp"),
        (15, 5,  "rRPRGkkGddddGkkGRRpp"),
        (16, 5,  "rRRpyyGddccddGyypRRr"),
        (17, 5,  "rrRpGGgddccbggGRRRrr"),
        (18, 6,  "rrRpgkddcccbkGRRrr"),
        (19, 6,  "rrrRdcddccbbRRRrr"),
        (20, 7,  "rrrRdcyGyyGyRRrr"),
        (21, 7,  "rrrRtLyYYyLlRRr"),
        (22, 8,  "rrrRLlGyyGLlRr"),
        (23, 8,  "rrrpPRRyGRRpr"),
        (24, 9,  "rrRRRR  RRRR"),
        (25, 9,  "rRRRr    rRRR"),
    ]
    _draw_rows(g, rows)
    _apply_outline(g)
    pygame.image.save(_render_grid(g), os.path.join(OUT_DIR, "knight_portrait.png"))


if __name__ == "__main__":
    pygame.init()
    generate_knight_sheets()
    generate_portrait()
    print(f"Высокодетализированный пиксель-арт Рыцаря-командира сохранён в {OUT_DIR}")
