"""
Модуль процедурной генерации ассетов в стиле Kingdom Rush.
Включает:
- Бесшовный луг с единым базовым тоном (без шахматки и резких стыков)
- Изгибающуюся реку с песчаными берегами и деревянным мостом
- Дорогу со скруглёнными углами и мягкой песчано-земляной обочиной
- Массивные лесные деревья (крупная крона и тени), пни с грибами и указатели
- Монументальный Портал 2x2 и Цитадель Замка 2x2
- Выразительные пиксельные иконки для плавающего HUD
"""

import os
import math
from typing import Dict, List, Tuple, Optional
import pygame
from settings import (
    TILE_SIZE,
    MAP_HEIGHT,
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
)

_tile_cache: Dict[str, pygame.Surface] = {}
_icon_cache: Dict[str, pygame.Surface] = {}
_font_cache: Dict[int, pygame.font.Font] = {}
_hero_anim_cache: Dict[str, Dict[str, List[pygame.Surface]]] = {}
_hero_portrait_cache: Dict[str, pygame.Surface] = {}
_hero_meta_cache: Dict[str, Dict[str, object]] = {}
_enemy_anim_cache: Dict[Tuple[str, bool], Dict[str, Dict[str, List[pygame.Surface]]]] = {}
_enemy_meta_cache: Dict[Tuple[str, bool], Dict[str, object]] = {}
_tower_packs_cache: Dict[str, Dict[str, object]] = {}


def _safe_convert(surf: pygame.Surface) -> pygame.Surface:
    """Безопасно конвертирует поверхность под формат видеорежима."""
    if pygame.display.get_surface() is not None:
        return surf.convert_alpha()
    return surf


def get_font(size: int = 12) -> pygame.font.Font:
    """Возвращает кэшированный чёткий шрифт с поддержкой кириллицы."""
    if size not in _font_cache:
        for font_name in ("tahoma", "verdana", "segoe ui", "consolas", "arial"):
            try:
                _font_cache[size] = pygame.font.SysFont(font_name, size, bold=True)
                break
            except Exception:
                continue
        if size not in _font_cache:
            _font_cache[size] = pygame.font.Font(None, size)
    return _font_cache[size]


# ==============================================================
# 1. ЕДИНЫЙ БЕСШОВНЫЙ ЛУГ (БЕЗ ШАХМАТКИ И БЕЗ СЕТОЧНЫХ ПЕРЕПАДОВ)
# ==============================================================

def _create_organic_grass_tile(variant: int) -> pygame.Surface:
    """
    Создаёт бесшовный средневековый луг.
    ВСЕ вариации используют СТРОГО один и тот же базовый цвет (45, 110, 52),
    что полностью устраняет эффект «шахматной доски» между соседними тайлами.
    """
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    base_green = (45, 110, 52)
    surf.fill(base_green)

    light_blade = (54, 124, 60)
    dark_blade = (38, 98, 44)

    # Мягкие единичные микро-детали без резких границ
    if variant == 0:
        # Чистый мягкий луг с лёгкими травинками
        surf.set_at((6, 8), light_blade)
        surf.set_at((7, 8), light_blade)
        surf.set_at((17, 18), dark_blade)
    elif variant == 1:
        # Аккуратный трилистник клевера
        surf.set_at((12, 11), light_blade)
        surf.set_at((13, 10), light_blade)
        surf.set_at((14, 11), light_blade)
        surf.set_at((13, 11), dark_blade)
    elif variant == 2:
        # Редкие полевые цветы (ромашка и колокольчик)
        surf.set_at((8, 14), (250, 250, 245))
        surf.set_at((10, 14), (250, 250, 245))
        surf.set_at((9, 13), (250, 250, 245))
        surf.set_at((9, 15), (250, 250, 245))
        surf.set_at((9, 14), (255, 225, 60))
        # Колокольчик
        surf.set_at((19, 6), (115, 175, 248))
        surf.set_at((20, 6), (150, 205, 255))
    elif variant == 3:
        # Мягкий мох и крошечный камешек
        surf.set_at((14, 15), (135, 145, 140))
        surf.set_at((15, 15), (160, 170, 165))
        surf.set_at((15, 16), (32, 75, 38))

    return surf


# ==============================================================
# 2. ИЗГИБАЮЩАЯСЯ РЕКА И ДЕРЕВЯННЫЙ МОСТ
# ==============================================================

def _create_river_tile(flow_type: str = 'straight', variant: int = 0) -> pygame.Surface:
    """
    Создаёт естественный тайл реки с мягким песчаным берегом и мерцающей водой.
    Поддерживает бесшовные изогнутые переходы: 'straight', 'n_w', 'e_s', 'n_e', 'w_s'.
    """
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    base_grass = (166, 176, 79)
    sandy = (165, 138, 95)
    sandy_dark = (135, 108, 70)
    water_mid = (45, 118, 185)
    water_deep = (32, 92, 155)
    water_light = (75, 158, 220)
    foam = (200, 235, 255)

    surf.fill(base_grass)

    if flow_type == 'straight':
        # Песчаные берега
        pygame.draw.rect(surf, sandy, (2, 0, 20, TILE_SIZE))
        pygame.draw.rect(surf, sandy_dark, (3, 0, 18, TILE_SIZE))
        # Водное зеркало
        pygame.draw.rect(surf, water_mid, (4, 0, 16, TILE_SIZE))
        pygame.draw.rect(surf, water_deep, (6, 0, 12, TILE_SIZE))
        # Волновые блики
        if variant == 0:
            pygame.draw.line(surf, water_light, (7, 6), (13, 6), 1)
            surf.set_at((10, 6), foam)
            pygame.draw.line(surf, water_light, (10, 16), (15, 16), 1)
        else:
            pygame.draw.line(surf, water_light, (9, 10), (15, 10), 1)
            surf.set_at((12, 10), foam)
            pygame.draw.line(surf, water_light, (6, 20), (12, 20), 1)

    elif flow_type == 'n_w':
        # Плавный изгиб с севера на запад (центр дуги в (0, 0))
        pygame.draw.circle(surf, sandy, (0, 0), 22)
        pygame.draw.circle(surf, sandy_dark, (0, 0), 20)
        pygame.draw.circle(surf, water_mid, (0, 0), 19)
        pygame.draw.circle(surf, water_deep, (0, 0), 16)
        pygame.draw.circle(surf, water_mid, (0, 0), 7)
        pygame.draw.circle(surf, sandy_dark, (0, 0), 5)
        pygame.draw.circle(surf, sandy, (0, 0), 4)
        pygame.draw.circle(surf, base_grass, (0, 0), 2)
        # Блик воды по дуге
        pygame.draw.arc(surf, water_light, (-12, -12, 24, 24), math.pi * 1.5, math.pi * 2.0, 1)

    elif flow_type == 'e_s':
        # Плавный изгиб с востока на юг (центр дуги в (24, 24))
        pygame.draw.circle(surf, sandy, (24, 24), 22)
        pygame.draw.circle(surf, sandy_dark, (24, 24), 20)
        pygame.draw.circle(surf, water_mid, (24, 24), 19)
        pygame.draw.circle(surf, water_deep, (24, 24), 16)
        pygame.draw.circle(surf, water_mid, (24, 24), 7)
        pygame.draw.circle(surf, sandy_dark, (24, 24), 5)
        pygame.draw.circle(surf, sandy, (24, 24), 4)
        pygame.draw.circle(surf, base_grass, (24, 24), 2)
        pygame.draw.arc(surf, water_light, (12, 12, 24, 24), math.pi * 0.5, math.pi, 1)

    elif flow_type == 'n_e':
        # Плавный изгиб с севера на восток (центр дуги в (24, 0))
        pygame.draw.circle(surf, sandy, (24, 0), 22)
        pygame.draw.circle(surf, sandy_dark, (24, 0), 20)
        pygame.draw.circle(surf, water_mid, (24, 0), 19)
        pygame.draw.circle(surf, water_deep, (24, 0), 16)
        pygame.draw.circle(surf, water_mid, (24, 0), 7)
        pygame.draw.circle(surf, sandy_dark, (24, 0), 5)
        pygame.draw.circle(surf, sandy, (24, 0), 4)
        pygame.draw.circle(surf, base_grass, (24, 0), 2)
        pygame.draw.arc(surf, water_light, (12, -12, 24, 24), math.pi, math.pi * 1.5, 1)

    elif flow_type == 'w_s':
        # Плавный изгиб с запада на юг (центр дуги в (0, 24))
        pygame.draw.circle(surf, sandy, (0, 24), 22)
        pygame.draw.circle(surf, sandy_dark, (0, 24), 20)
        pygame.draw.circle(surf, water_mid, (0, 24), 19)
        pygame.draw.circle(surf, water_deep, (0, 24), 16)
        pygame.draw.circle(surf, water_mid, (0, 24), 7)
        pygame.draw.circle(surf, sandy_dark, (0, 24), 5)
        pygame.draw.circle(surf, sandy, (0, 24), 4)
        pygame.draw.circle(surf, base_grass, (0, 24), 2)
        pygame.draw.arc(surf, water_light, (-12, 12, 24, 24), 0, math.pi * 0.5, 1)

    return surf


def _create_bridge_tile() -> pygame.Surface:
    """Деревянный мост через реку: массивные дубовые доски, перила и сваи."""
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    surf.blit(_create_river_tile('straight', 0), (0, 0))

    wood_dark = (72, 46, 24)
    wood_plank = (136, 94, 54)
    wood_hi = (175, 126, 78)
    iron_nail = (195, 170, 120)

    # 1. Тень от моста на воде
    pygame.draw.rect(surf, (18, 42, 70), (0, 2, TILE_SIZE, 20))

    # 2. Поперечные дубовые доски
    for x in range(1, TILE_SIZE - 1, 4):
        pygame.draw.rect(surf, wood_plank, (x, 3, 3, 18))
        pygame.draw.line(surf, wood_hi, (x, 3), (x + 2, 3), 1)
        pygame.draw.line(surf, wood_dark, (x + 2, 4), (x + 2, 20), 1)
        surf.set_at((x + 1, 5), iron_nail)
        surf.set_at((x + 1, 18), iron_nail)

    # 3. Верхние и нижние перила
    rail_color = (118, 78, 42)
    rail_hi = (165, 116, 70)
    pygame.draw.rect(surf, rail_color, (0, 2, TILE_SIZE, 3))
    pygame.draw.line(surf, rail_hi, (0, 2), (TILE_SIZE, 2), 1)
    pygame.draw.rect(surf, rail_color, (0, 19, TILE_SIZE, 3))
    pygame.draw.line(surf, rail_hi, (0, 19), (TILE_SIZE, 19), 1)

    # Угловые опорные столбы
    for sx in (0, TILE_SIZE - 3):
        pygame.draw.rect(surf, (58, 36, 18), (sx, 1, 3, 5))
        pygame.draw.rect(surf, (58, 36, 18), (sx, 18, 3, 5))

    return surf


def _create_wide_bridge_tile() -> pygame.Surface:
    """Широкий деревянный мост высотой в 3 тайла (24x72 px) для 3-тайловой дороги."""
    h = TILE_SIZE * 3
    surf = pygame.Surface((TILE_SIZE, h), pygame.SRCALPHA)
    for row_idx in range(3):
        surf.blit(_create_river_tile('straight', row_idx % 2), (0, row_idx * TILE_SIZE))

    wood_dark = (72, 46, 24)
    wood_plank = (136, 94, 54)
    wood_hi = (175, 126, 78)
    iron_nail = (195, 170, 120)

    # 1. Тень от широкого моста на воде
    pygame.draw.rect(surf, (18, 42, 70), (0, 2, TILE_SIZE, h - 4))

    # 2. Непрерывный дубовый настил по всей ширине дороги (3 тайла)
    deck_top = 3
    deck_h = h - 6
    for x in range(1, TILE_SIZE - 1, 4):
        pygame.draw.rect(surf, wood_plank, (x, deck_top, 3, deck_h))
        pygame.draw.line(surf, wood_hi, (x, deck_top), (x + 2, deck_top), 1)
        pygame.draw.line(surf, wood_dark, (x + 2, deck_top + 1), (x + 2, deck_top + deck_h - 1), 1)
        for ny in (5, TILE_SIZE - 2, TILE_SIZE + 2, TILE_SIZE * 2 - 2, TILE_SIZE * 2 + 2, h - 6):
            surf.set_at((x + 1, ny), iron_nail)

    # Тонкие поперечные стыки досок на уровне границ тайлов
    for seam_y in (TILE_SIZE, TILE_SIZE * 2):
        pygame.draw.line(surf, (96, 62, 34), (0, seam_y), (TILE_SIZE - 1, seam_y), 1)

    # 3. Внешние перила только сверху (на 1-м тайле) и снизу (на 3-м тайле)
    rail_color = (118, 78, 42)
    rail_hi = (165, 116, 70)
    pygame.draw.rect(surf, rail_color, (0, 2, TILE_SIZE, 3))
    pygame.draw.line(surf, rail_hi, (0, 2), (TILE_SIZE - 1, 2), 1)
    pygame.draw.rect(surf, rail_color, (0, h - 5, TILE_SIZE, 3))
    pygame.draw.line(surf, rail_hi, (0, h - 5), (TILE_SIZE - 1, h - 5), 1)

    # Опорные столбы по краям моста
    for sx in (0, TILE_SIZE - 3):
        pygame.draw.rect(surf, (58, 36, 18), (sx, 1, 3, 5))
        pygame.draw.rect(surf, (58, 36, 18), (sx, h - 6, 3, 5))

    return surf


# ==============================================================
# 3. ДОРОГА С МЯГКОЙ ОБОЧИНОЙ И ПЕСЧАНО-ГРУНТОВОЙ ТРОПОЙ
# ==============================================================

def _create_road_segment(style: str, variant: int = 0) -> pygame.Surface:
    """
    Создаёт единый бесшовный фрагмент песчано-грунтовой дороги (без плиточных кирпичей):
    style: 'h', 'v', 'c_se', 'c_sw', 'c_ne', 'c_nw'.
    """
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    surf.blit(_create_organic_grass_tile(0), (0, 0))

    dirt_border = (98, 72, 46)     # Тёмная земляная окантовка
    dirt_mid    = (136, 106, 70)   # Мягкий земляной переход
    sand_body   = (185, 154, 110)  # Тёплый песочный центр
    sand_light  = (205, 176, 132)  # Светлый утоптанный песок
    sand_rut    = (168, 136, 96)   # Лёгкая колея

    if style == 'h':
        # Горизонтальная песчаная дорога
        pygame.draw.rect(surf, dirt_border, (0, 1, TILE_SIZE, 22))
        pygame.draw.rect(surf, dirt_mid, (0, 3, TILE_SIZE, 18))
        pygame.draw.rect(surf, sand_body, (0, 5, TILE_SIZE, 14))
        pygame.draw.rect(surf, sand_light, (0, 8, TILE_SIZE, 8))
        # Колея телег
        pygame.draw.line(surf, sand_rut, (0, 9), (TILE_SIZE, 9), 1)
        pygame.draw.line(surf, sand_rut, (0, 15), (TILE_SIZE, 15), 1)
        # Мелкие камушки
        if variant == 0:
            surf.set_at((6, 7), (225, 205, 175))
            surf.set_at((6, 8), (82, 62, 42))
            surf.set_at((17, 16), (225, 205, 175))
            surf.set_at((17, 17), (82, 62, 42))
        elif variant == 1:
            surf.set_at((12, 6), (225, 205, 175))
            surf.set_at((12, 7), (82, 62, 42))
            # Трещинка
            pygame.draw.line(surf, (130, 100, 68), (18, 11), (21, 12), 1)
        else:
            surf.set_at((4, 16), (225, 205, 175))
            surf.set_at((4, 17), (82, 62, 42))
            pygame.draw.line(surf, (130, 100, 68), (14, 10), (16, 10), 1)

    elif style == 'v':
        # Вертикальная песчаная дорога
        pygame.draw.rect(surf, dirt_border, (1, 0, 22, TILE_SIZE))
        pygame.draw.rect(surf, dirt_mid, (3, 0, 18, TILE_SIZE))
        pygame.draw.rect(surf, sand_body, (5, 0, 14, TILE_SIZE))
        pygame.draw.rect(surf, sand_light, (8, 0, 8, TILE_SIZE))
        # Колея телег
        pygame.draw.line(surf, sand_rut, (9, 0), (9, TILE_SIZE), 1)
        pygame.draw.line(surf, sand_rut, (15, 0), (15, TILE_SIZE), 1)
        # Мелкие камушки
        if variant == 0:
            surf.set_at((7, 6), (225, 205, 175))
            surf.set_at((7, 7), (82, 62, 42))
            surf.set_at((16, 18), (225, 205, 175))
            surf.set_at((16, 19), (82, 62, 42))
        elif variant == 1:
            surf.set_at((7, 14), (225, 205, 175))
            surf.set_at((7, 15), (82, 62, 42))
            pygame.draw.line(surf, (130, 100, 68), (11, 8), (11, 11), 1)
        else:
            surf.set_at((16, 8), (225, 205, 175))
            surf.set_at((16, 9), (82, 62, 42))
            pygame.draw.line(surf, (130, 100, 68), (10, 17), (10, 19), 1)

    else:
        # Плавные скруглённые повороты без пустых ромбиков
        corner_defs = {
            'c_se': (24, 24, (0, 0)),
            'c_sw': (0, 24, (24, 0)),
            'c_ne': (24, 0, (0, 24)),
            'c_nw': (0, 0, (24, 24)),
        }
        cx, cy, grass_corner = corner_defs.get(style, (24, 24, (0, 0)))
        pygame.draw.circle(surf, dirt_border, (cx, cy), 23)
        pygame.draw.circle(surf, dirt_mid, (cx, cy), 21)
        pygame.draw.circle(surf, sand_body, (cx, cy), 19)
        pygame.draw.circle(surf, sand_light, (cx, cy), 16)
        pygame.draw.circle(surf, sand_body, (cx, cy), 7)
        pygame.draw.circle(surf, dirt_mid, (cx, cy), 5)
        pygame.draw.circle(surf, dirt_border, (cx, cy), 3)
        pygame.draw.circle(surf, (36, 118, 48), (cx, cy), 1)

    return surf


def create_continuous_road_surface(road_nodes: list) -> pygame.Surface:
    """
    Создаёт единый плавный слой дороги на весь экран (640x360 px) в стиле Kingdom Rush:
    - Тёплый песчаный центр с колеёй телег.
    - Аккуратная тёмная земляная окантовка по краям.
    - Мягкие скруглённые стыки и повороты (через толстые линии и круги на стыках).
    - Редкие мелкие камушки и трещинки вместо повторяющихся кирпичиков.
    """
    surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)

    def to_px(c, r):
        return (MAP_OFFSET_X + c * TILE_SIZE + TILE_SIZE // 2,
                MAP_OFFSET_Y + r * TILE_SIZE + TILE_SIZE // 2)

    pts = [to_px(c, r) for c, r in road_nodes]

    dirt_border = (98, 72, 46)     # Тёмная земляная окантовка
    dirt_mid    = (136, 106, 70)   # Мягкий земляной переход
    sand_body   = (185, 154, 110)  # Тёплый песочный центр
    sand_light  = (205, 176, 132)  # Светлый утоптанный песок
    sand_rut    = (168, 136, 96)   # Лёгкая колея

    layers = [
        (dirt_border, 22, 11),
        (dirt_mid,    18, 9),
        (sand_body,   14, 7),
        (sand_light,  8,  4),
    ]

    for color, width, radius in layers:
        # 1. Скругления на стыках и поворотах
        for p in pts:
            pygame.draw.circle(surf, color, p, radius)
        # 2. Прямые участки дороги
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            if y1 == y2:
                rx = min(x1, x2)
                rw = abs(x2 - x1)
                ry = y1 - radius
                rh = width
                pygame.draw.rect(surf, color, (rx, ry, rw, rh))
            else:
                rx = x1 - radius
                rw = width
                ry = min(y1, y2)
                rh = abs(y2 - y1)
                pygame.draw.rect(surf, color, (rx, ry, rw, rh))

    # 3. Лёгкая колея телег (два тонких следа вдоль прямых участков)
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        if y1 == y2:
            rx = min(x1, x2)
            rw = abs(x2 - x1)
            pygame.draw.line(surf, sand_rut, (rx + 4, y1 - 3), (rx + rw - 4, y1 - 3), 1)
            pygame.draw.line(surf, sand_rut, (rx + 4, y1 + 3), (rx + rw - 4, y1 + 3), 1)
        else:
            ry = min(y1, y2)
            rh = abs(y2 - y1)
            pygame.draw.line(surf, sand_rut, (x1 - 3, ry + 4), (x1 - 3, ry + rh - 4), 1)
            pygame.draw.line(surf, sand_rut, (x1 + 3, ry + 4), (x1 + 3, ry + rh - 4), 1)

    # 4. Редкие мелкие камушки и трещинки (детерминированный генератор)
    import random
    rng = random.Random(42)
    pebble_sh = (82, 62, 42)
    pebble_hi = (225, 205, 175)
    crack_col = (130, 100, 68)

    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        length = int(abs(x2 - x1) + abs(y2 - y1))
        num_details = length // 35
        for _ in range(num_details):
            t = rng.uniform(0.15, 0.85)
            offset = rng.randint(-4, 4)
            if y1 == y2:
                dx = int(min(x1, x2) + t * abs(x2 - x1))
                dy = y1 + offset
            else:
                dx = x1 + offset
                dy = int(min(y1, y2) + t * abs(y2 - y1))
            # Чередуем камушек или трещинку
            if rng.random() < 0.6:
                surf.set_at((dx, dy), pebble_hi)
                surf.set_at((dx, dy + 1), pebble_sh)
                surf.set_at((dx + 1, dy + 1), pebble_sh)
            else:
                surf.set_at((dx, dy), crack_col)
                surf.set_at((dx + 1, dy), crack_col)
                surf.set_at((dx + 2, dy + (1 if offset > 0 else -1)), crack_col)

    return surf


# ==============================================================
# 4. СТРОИТЕЛЬНЫЕ ПЛОЩАДКИ (АККУРАТНЫЙ КАМЕННЫЙ ПЬЕДЕСТАЛ 30x22 px)
# ==============================================================

def _create_build_spot_tile() -> pygame.Surface:
    """
    Аккуратный, объёмный круглый (слегка овальный в перспективе) каменный пьедестал
    в стиле Kingdom Rush:
    - Мягкая тень снизу на траве.
    - Светлый объёмный ободок со световым бликом сверху-слева.
    - Слегка углублённый центр (чаша) без каких-либо значков, молотков или рисунков.
    """
    surf = pygame.Surface((30, 22), pygame.SRCALPHA)

    # 1. Мягкая тень под основанием
    pygame.draw.ellipse(surf, (16, 42, 20, 130), (2, 7, 26, 13))

    # 2. Боковая каменная грань (3D цоколь пьедестала)
    wall_dark = (68, 54, 40)
    wall_mid = (88, 72, 54)
    for dy in range(4, 0, -1):
        c = wall_dark if dy >= 3 else wall_mid
        pygame.draw.ellipse(surf, c, (2, 3 + dy, 26, 13))

    # 3. Объёмный верхний ободок пьедестала
    rim_dark = (112, 92, 72)
    rim_mid = (168, 148, 118)
    rim_light = (205, 186, 152)
    rim_hi = (235, 220, 190)

    # Базовый диск ободка
    pygame.draw.ellipse(surf, rim_dark, (2, 3, 26, 13))
    pygame.draw.ellipse(surf, rim_light, (2, 3, 26, 12))
    pygame.draw.ellipse(surf, rim_mid, (3, 4, 24, 10))

    # Световые блики на ободке (сверху-слева)
    pygame.draw.line(surf, rim_hi, (8, 3), (16, 3), 1)
    pygame.draw.line(surf, rim_hi, (5, 4), (7, 4), 1)
    pygame.draw.line(surf, rim_hi, (17, 4), (20, 4), 1)

    # Теневые точки на ободке (снизу-справа)
    pygame.draw.line(surf, wall_dark, (8, 15), (20, 15), 1)

    # 4. Углублённый центр (аккуратная круглая чаша без молотков и символов)
    recess_shadow = (75, 60, 45)  # глубокая тень под верхним ободком
    recess_floor = (145, 124, 98)   # песчано-каменное дно
    recess_warm = (162, 138, 110)

    pygame.draw.ellipse(surf, recess_shadow, (5, 5, 20, 8))
    pygame.draw.ellipse(surf, recess_floor, (5, 6, 20, 7))
    pygame.draw.ellipse(surf, recess_warm, (6, 7, 18, 5))

    # Тонкие акцентные пиксели на дне углубления
    surf.set_at((14, 8), (170, 146, 118))
    surf.set_at((15, 8), (170, 146, 118))

    return surf


# ==============================================================
# 5. ДЕКОРАЦИИ: КРУПНЫЕ ДЕРЕВЬЯ (30x38 px), ВАЛУНЫ, ПНИ, УКАЗАТЕЛЬ
# ==============================================================

def _create_grand_tree_obstacle() -> pygame.Surface:
    """
    Могучий раскидистый лесной дуб (30x38 px) с многоярусной кроной.
    Крона выступает на 14 px выше тайла, создавая глубокий навес.
    """
    w, h = 30, 38
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # 1. Тень под деревом (y=28..36)
    pygame.draw.ellipse(surf, (18, 48, 22, 150), (2, 28, 26, 9))

    # 2. Мощный кряжистый ствол и корни
    trunk_dark = (52, 32, 18)
    trunk_mid = (82, 52, 28)
    trunk_light = (118, 76, 42)

    # Корни
    pygame.draw.polygon(surf, trunk_dark, [(11, 25), (6, 33), (9, 33), (13, 27)])
    pygame.draw.polygon(surf, trunk_dark, [(19, 25), (24, 33), (21, 33), (17, 27)])
    # Ствол
    pygame.draw.rect(surf, trunk_dark, (12, 18, 7, 13))
    pygame.draw.rect(surf, trunk_mid, (13, 18, 5, 12))
    pygame.draw.line(surf, trunk_light, (14, 19), (14, 29), 1)

    # 3. Многослойная пышная крона
    c_shadow = (20, 52, 24)
    c_dark = (30, 78, 34)
    c_mid = (45, 112, 48)
    c_light = (74, 158, 70)
    c_hi = (112, 198, 102)

    # Нижний затененный ярус
    pygame.draw.circle(surf, c_shadow, (8, 18), 8)
    pygame.draw.circle(surf, c_shadow, (22, 18), 8)
    pygame.draw.circle(surf, c_dark, (15, 17), 10)

    # Средний ярус кроны
    pygame.draw.circle(surf, c_dark, (9, 16), 7)
    pygame.draw.circle(surf, c_mid, (8, 15), 6)
    pygame.draw.circle(surf, c_dark, (21, 16), 7)
    pygame.draw.circle(surf, c_mid, (20, 15), 6)

    # Верхняя центральная шапка
    pygame.draw.circle(surf, c_dark, (15, 10), 10)
    pygame.draw.circle(surf, c_mid, (15, 10), 9)
    pygame.draw.circle(surf, c_light, (13, 8), 7)

    # Солнечные блики листвы
    pygame.draw.circle(surf, c_hi, (11, 6), 3)
    surf.set_at((10, 5), (148, 232, 135))
    surf.set_at((16, 7), c_hi)
    surf.set_at((21, 13), c_light)

    return surf


def _create_pine_obstacle() -> pygame.Surface:
    """
    Вековая остроконечная ель (30x38 px) с 4 ярусами хвойных лап.
    """
    w, h = 30, 38
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # Тень
    pygame.draw.ellipse(surf, (18, 48, 22, 150), (4, 29, 22, 8))
    trunk_dark = (52, 32, 18)
    pygame.draw.rect(surf, trunk_dark, (13, 22, 5, 11))

    p_shadow = (14, 45, 25)
    p_dark = (22, 65, 36)
    p_mid = (34, 92, 52)
    p_light = (58, 134, 78)
    p_hi = (95, 185, 115)

    # 1. Нижний ярус хвои
    pygame.draw.polygon(surf, p_shadow, [(3, 27), (27, 27), (15, 17)])
    pygame.draw.polygon(surf, p_dark, [(4, 26), (26, 26), (15, 17)])
    pygame.draw.polygon(surf, p_mid, [(5, 25), (16, 25), (15, 18)])

    # 2. Второй ярус
    pygame.draw.polygon(surf, p_shadow, [(5, 20), (25, 20), (15, 11)])
    pygame.draw.polygon(surf, p_dark, [(6, 19), (24, 19), (15, 11)])
    pygame.draw.polygon(surf, p_mid, [(7, 18), (16, 18), (15, 12)])

    # 3. Третий ярус
    pygame.draw.polygon(surf, p_shadow, [(7, 13), (23, 13), (15, 5)])
    pygame.draw.polygon(surf, p_dark, [(8, 12), (22, 12), (15, 5)])
    pygame.draw.polygon(surf, p_mid, [(9, 11), (16, 11), (15, 6)])

    # 4. Верхушка
    pygame.draw.polygon(surf, p_shadow, [(9, 7), (21, 7), (15, 2)])
    pygame.draw.polygon(surf, p_dark, [(10, 6), (20, 6), (15, 2)])
    pygame.draw.polygon(surf, p_light, [(11, 5), (15, 5), (15, 2)])
    surf.set_at((15, 2), p_hi)

    return surf


def _create_rock_obstacle() -> pygame.Surface:
    """Древний скальный валун (24x24 px) с фактурой гранита, глубокой трещиной и мхом."""
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

    # Тень под валуном
    pygame.draw.ellipse(surf, (18, 48, 22, 140), (3, 16, 18, 7))

    rock_shadow = (34, 40, 50)
    rock_mid = (62, 72, 86)
    rock_light = (100, 114, 132)
    rock_hi = (135, 148, 168)
    moss = (48, 112, 42)
    moss_hi = (74, 146, 62)

    pts = [(4, 16), (3, 11), (7, 5), (14, 4), (19, 8), (20, 15), (14, 19), (6, 18)]
    pygame.draw.polygon(surf, rock_shadow, pts)
    pygame.draw.polygon(surf, rock_mid, [(p[0] + 1, p[1] - 1) for p in pts[:6]] + [(15, 16), (6, 17)])

    pygame.draw.polygon(surf, rock_light, [(7, 6), (13, 5), (17, 8), (14, 11), (8, 10)])
    surf.set_at((10, 6), rock_hi)
    surf.set_at((11, 6), rock_hi)
    pygame.draw.line(surf, (22, 26, 34), (12, 9), (15, 14), 1)

    # Замшелые островки
    surf.set_at((6, 6), moss_hi)
    surf.set_at((7, 7), moss)
    surf.set_at((16, 16), moss)
    surf.set_at((17, 15), moss_hi)
    return surf


def _create_stump_obstacle() -> pygame.Surface:
    """Старый замшелый пень с годичными кольцами и красными мухоморами."""
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

    # Тень
    pygame.draw.ellipse(surf, (18, 48, 22, 140), (3, 15, 18, 6))

    # Тело пня
    wood_dark = (65, 40, 22)
    wood_mid = (95, 62, 36)
    wood_top = (145, 105, 65)

    pygame.draw.rect(surf, wood_dark, (6, 10, 12, 8))
    pygame.draw.rect(surf, wood_mid, (7, 10, 10, 7))

    # Спил с кольцами
    pygame.draw.ellipse(surf, wood_dark, (6, 8, 12, 6))
    pygame.draw.ellipse(surf, wood_top, (7, 9, 10, 4))
    surf.set_at((11, 10), wood_dark)  # сердцевина

    # Мох у корней
    surf.set_at((5, 16), (55, 125, 48))
    surf.set_at((6, 15), (75, 150, 60))

    # Красный мухоморчик рядом с белыми крапинками
    surf.set_at((17, 15), (230, 230, 220))  # ножка
    pygame.draw.circle(surf, (225, 40, 40), (17, 13), 2)  # шляпка
    surf.set_at((17, 12), (255, 255, 255))  # точка

    return surf


def _create_signpost_prop() -> pygame.Surface:
    """Деревянный указатель у дороги: стрелка с направлением к Замку."""
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    # Столбик
    pygame.draw.rect(surf, (72, 45, 25), (11, 8, 3, 14))
    # Деревянная стрелка-указатель вправо
    arrow_pts = [(5, 6), (17, 6), (21, 9), (17, 12), (5, 12)]
    pygame.draw.polygon(surf, (140, 95, 55), arrow_pts)
    pygame.draw.polygon(surf, (85, 52, 28), arrow_pts, 1)
    # Блик на доске
    pygame.draw.line(surf, (175, 125, 75), (6, 7), (16, 7), 1)
    return surf


# ==============================================================
# 6. ВЕЛИЧЕСТВЕННЫЙ ЗАМОК 3x3 И ИНФЕРНАЛЬНЫЙ ПОРТАЛ 2x2
# ==============================================================

def _create_castle_3x3() -> pygame.Surface:
    """
    Величественная крепость Замка Королевства (72x72 px / 3x3 тайла):
    - Тёплые стены из песчаника с рельефной кирпичной кладкой
    - Две круглые фланговые башни с коническими крышами из красной черепицы и шпилями
    - Центральная стена с боевыми зубцами (battlements)
    - Массивная каменная арка с железной опускной решёткой (герсой)
    - Горящие факелы по бокам ворот с золотым сиянием
    - Развевающиеся королевские знамёна и золотой герб
    - Мягкая падающая тень у подножия цитадели
    """
    surf = pygame.Surface((72, 72), pygame.SRCALPHA)

    # 1. Мягкая тень у основания крепости на траве
    pygame.draw.ellipse(surf, (18, 45, 22, 150), (4, 56, 64, 16))

    # Цветовая палитра тёплого замкового камня
    stone_dark = (65, 55, 48)
    stone_base = (135, 120, 105)
    stone_light = (175, 160, 142)
    stone_hi = (215, 202, 185)

    roof_dark = (125, 22, 26)
    roof_base = (185, 38, 42)
    roof_light = (225, 65, 70)
    gold = (245, 205, 50)
    iron = (45, 48, 55)

    # 2. Центральная стена (основа цитадели)
    pygame.draw.rect(surf, stone_dark, (16, 22, 40, 46))
    pygame.draw.rect(surf, stone_base, (18, 24, 36, 42))

    # Каменная кладка (горизонтальные и вертикальные швы)
    for y in range(28, 62, 7):
        pygame.draw.line(surf, stone_dark, (18, y), (53, y), 1)
        offset = 4 if (y // 7) % 2 == 0 else 0
        for x in range(22 + offset, 52, 9):
            pygame.draw.line(surf, stone_dark, (x, y - 6), (x, y), 1)

    # 3. Центральные зубцы стены (battlements)
    for bx in (20, 28, 36, 44):
        pygame.draw.rect(surf, stone_dark, (bx, 17, 6, 6))
        pygame.draw.rect(surf, stone_base, (bx + 1, 18, 4, 5))
        pygame.draw.line(surf, stone_hi, (bx + 1, 18), (bx + 4, 18), 1)

    # 4. Левая круглая башня (x=4..22, y=14..68)
    pygame.draw.rect(surf, stone_dark, (4, 20, 18, 48))
    pygame.draw.rect(surf, stone_base, (6, 22, 14, 44))
    # Цилиндрическая светотень на башне
    pygame.draw.line(surf, stone_hi, (6, 22), (6, 65), 1)
    pygame.draw.line(surf, stone_light, (7, 22), (7, 65), 2)
    pygame.draw.line(surf, stone_dark, (18, 22), (18, 65), 2)
    # Бойница
    pygame.draw.rect(surf, iron, (11, 38, 3, 7))

    # Коническая крыша левой башни с красной черепицей
    roof_left_pts = [(13, 3), (3, 21), (23, 21)]
    pygame.draw.polygon(surf, roof_dark, [(p[0], p[1] + 1) for p in roof_left_pts] + [(13, 2)])
    pygame.draw.polygon(surf, roof_base, roof_left_pts)
    pygame.draw.polygon(surf, roof_light, [(13, 5), (6, 20), (13, 20)])
    pygame.draw.polygon(surf, roof_dark, [(13, 5), (13, 20), (20, 20)])
    # Шпиль с золотым шаром
    pygame.draw.line(surf, gold, (13, 0), (13, 4), 1)
    surf.set_at((13, 0), (255, 240, 150))

    # 5. Правая круглая башня (x=50..68, y=14..68)
    pygame.draw.rect(surf, stone_dark, (50, 20, 18, 48))
    pygame.draw.rect(surf, stone_base, (52, 22, 14, 44))
    pygame.draw.line(surf, stone_hi, (52, 22), (52, 65), 1)
    pygame.draw.line(surf, stone_light, (53, 22), (53, 65), 2)
    pygame.draw.line(surf, stone_dark, (64, 22), (64, 65), 2)
    # Бойница
    pygame.draw.rect(surf, iron, (57, 38, 3, 7))

    # Коническая крыша правой башни
    roof_right_pts = [(59, 3), (49, 21), (69, 21)]
    pygame.draw.polygon(surf, roof_dark, [(p[0], p[1] + 1) for p in roof_right_pts] + [(59, 2)])
    pygame.draw.polygon(surf, roof_base, roof_right_pts)
    pygame.draw.polygon(surf, roof_light, [(59, 5), (52, 20), (59, 20)])
    pygame.draw.polygon(surf, roof_dark, [(59, 5), (59, 20), (66, 20)])
    # Шпиль
    pygame.draw.line(surf, gold, (59, 0), (59, 4), 1)
    surf.set_at((59, 0), (255, 240, 150))

    # 6. Большие арочные замковые ворота (портал в центре)
    pygame.draw.rect(surf, stone_dark, (24, 40, 24, 28))
    pygame.draw.ellipse(surf, stone_dark, (24, 34, 24, 18))
    # Внутренний проём ворот
    pygame.draw.rect(surf, (22, 18, 24), (26, 42, 20, 26))
    pygame.draw.ellipse(surf, (22, 18, 24), (26, 36, 20, 16))

    # Железная решётка (герса / portcullis)
    for gx in (29, 32, 35, 38, 42):
        pygame.draw.line(surf, (95, 105, 120), (gx, 40), (gx, 67), 1)
        surf.set_at((gx, 67), (180, 195, 215))
    for gy in (44, 50, 56, 62):
        pygame.draw.line(surf, (80, 90, 105), (27, gy), (44, gy), 1)

    # 7. Факелы по бокам ворот
    for tx in (23, 48):
        pygame.draw.line(surf, (55, 35, 20), (tx, 48), (tx, 54), 1)
        surf.set_at((tx, 47), (255, 220, 60))
        surf.set_at((tx, 46), (255, 120, 30))
        surf.set_at((tx + 1, 47), (255, 70, 20))

    # 8. Развевающиеся королевские флаги на шпилях
    flag_l = [(13, 1), (5, 4), (13, 7)]
    pygame.draw.polygon(surf, roof_base, flag_l)
    pygame.draw.line(surf, gold, (13, 4), (7, 4), 1)

    flag_r = [(59, 1), (51, 4), (59, 7)]
    pygame.draw.polygon(surf, roof_base, flag_r)
    pygame.draw.line(surf, gold, (59, 4), (53, 4), 1)

    # Золотой королевский герб над аркой ворот
    crest_pts = [(34, 31), (38, 31), (39, 34), (36, 37), (33, 34)]
    pygame.draw.polygon(surf, gold, crest_pts)
    surf.set_at((36, 33), roof_base)

    return surf


def _create_portal_2x2() -> pygame.Surface:
    """Устаревший портал (заменён на открытый выход врагов с левого края карты)."""
    return pygame.Surface((48, 48), pygame.SRCALPHA)


# ==============================================================
# 7. БОКОВОЙ ЛЕСНОЙ МАССИВ
# ==============================================================

def _create_side_forest_strip(width: int = 8, height: int = MAP_HEIGHT) -> pygame.Surface:
    """Заполняет боковой отступ 8px плотным лесом с объёмной кроной под тон травы 1 Tiles/."""
    surf = pygame.Surface((width, height))
    c_deep = (166, 176, 79)
    c_mid = (118, 138, 52)
    c_light = (148, 168, 64)
    surf.fill(c_deep)

    for y in range(0, height, 16):
        pygame.draw.circle(surf, c_mid, (width // 2, y + 8), 7)
        pygame.draw.circle(surf, c_light, (width // 2, y + 6), 5)
        pygame.draw.rect(surf, (82, 54, 30), (width // 2 - 1, y + 12, 3, 5))

    return surf


# ==============================================================
# 8. КРАСИВЫЕ ОБЪЁМНЫЕ ИКОНКИ ДЛЯ ФЭНТЕЗИ-HUD
# ==============================================================

def _create_icon_heart_3d() -> pygame.Surface:
    """Рубиновое огранённое сердце с ярким бликом 14x14."""
    surf = pygame.Surface((14, 14), pygame.SRCALPHA)
    red_dark = (145, 18, 24)
    red = (215, 32, 42)
    red_hi = (255, 120, 130)
    white_shine = (255, 240, 240)

    pygame.draw.circle(surf, red_dark, (4, 5), 4)
    pygame.draw.circle(surf, red_dark, (9, 5), 4)
    pygame.draw.polygon(surf, red_dark, [(1, 6), (12, 6), (7, 12)])

    pygame.draw.circle(surf, red, (4, 5), 3)
    pygame.draw.circle(surf, red, (9, 5), 3)
    pygame.draw.polygon(surf, red, [(2, 6), (11, 6), (7, 11)])

    surf.set_at((3, 3), white_shine)
    surf.set_at((4, 3), white_shine)
    surf.set_at((3, 4), red_hi)
    return surf


def _create_icon_coin_3d() -> pygame.Surface:
    """Золотая монета с чеканным ободком и ярким сиянием 14x14."""
    surf = pygame.Surface((14, 14), pygame.SRCALPHA)
    gold_dark = (155, 105, 15)
    gold = (245, 195, 35)
    gold_hi = (255, 235, 110)
    white = (255, 255, 230)

    pygame.draw.circle(surf, gold_dark, (7, 7), 6)
    pygame.draw.circle(surf, gold, (7, 7), 5)
    pygame.draw.circle(surf, gold_hi, (6, 6), 3)
    surf.set_at((5, 4), white)
    surf.set_at((6, 4), white)
    return surf


def _create_icon_skull_3d() -> pygame.Surface:
    """Рельефный череп 12x12 со светотенью для счётчика волн."""
    surf = pygame.Surface((12, 12), pygame.SRCALPHA)
    bone_sh = (175, 168, 150)
    bone = (240, 235, 220)
    bone_hi = (255, 255, 245)
    dark = (38, 28, 22)

    pygame.draw.circle(surf, bone_sh, (6, 5), 4)
    pygame.draw.circle(surf, bone, (6, 5), 3)
    pygame.draw.rect(surf, bone, (4, 7, 5, 3))
    surf.set_at((5, 3), bone_hi)

    surf.set_at((4, 5), dark)
    surf.set_at((7, 5), dark)
    surf.set_at((5, 9), dark)
    surf.set_at((7, 9), dark)
    return surf


def _create_icon_sound_3d() -> pygame.Surface:
    """Объёмная иконка динамика звука 14x14."""
    surf = pygame.Surface((14, 14), pygame.SRCALPHA)
    gold = (245, 215, 80)
    gold_hi = (255, 240, 160)
    pygame.draw.rect(surf, gold, (2, 4, 3, 6))
    pygame.draw.polygon(surf, gold, [(5, 4), (9, 1), (9, 12), (5, 9)])
    pygame.draw.arc(surf, gold_hi, (7, 2, 5, 10), -1.1, 1.1, 1)
    return surf


def _create_icon_pause_3d() -> pygame.Surface:
    """Иконка паузы 14x14."""
    surf = pygame.Surface((14, 14), pygame.SRCALPHA)
    gold = (245, 215, 80)
    pygame.draw.rect(surf, gold, (3, 2, 3, 10))
    pygame.draw.rect(surf, gold, (8, 2, 3, 10))
    return surf


def _create_icon_fast_forward_3d() -> pygame.Surface:
    """Иконка ускорения/старта волны (двойная золотая стрелка) 14x14."""
    surf = pygame.Surface((14, 14), pygame.SRCALPHA)
    gold = (255, 225, 75)
    gold_hi = (255, 245, 160)
    pygame.draw.polygon(surf, gold, [(2, 2), (7, 7), (2, 12)])
    pygame.draw.polygon(surf, gold_hi, [(3, 3), (6, 7), (3, 11)])
    pygame.draw.polygon(surf, gold, [(7, 2), (12, 7), (7, 12)])
    pygame.draw.polygon(surf, gold_hi, [(8, 3), (11, 7), (8, 11)])
    return surf


# ==============================================================
# 9. ИНИЦИАЛИЗАЦИЯ И ДОСТУП К АССЕТАМ
# ==============================================================

def make_outside_transparent(
    surf: pygame.Surface,
    bg_color: Tuple[int, int, int] = (255, 255, 255),
    tolerance: int = 15,
) -> pygame.Surface:
    """
    Удаляет белый фон ТОЛЬКО снаружи спрайта с помощью flood-fill от границ изображения.
    Белые блики, таблички и детали внутри контура остаются нетронутыми!
    """
    w, h = surf.get_size()
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    out.blit(surf, (0, 0))

    def is_bg(x: int, y: int) -> bool:
        c = out.get_at((x, y))
        return (abs(c[0] - bg_color[0]) <= tolerance and
                abs(c[1] - bg_color[1]) <= tolerance and
                abs(c[2] - bg_color[2]) <= tolerance)

    visited = bytearray(w * h)
    queue = []

    for x in range(w):
        if is_bg(x, 0):
            queue.append((x, 0))
            visited[x] = 1
        if is_bg(x, h - 1):
            queue.append((x, h - 1))
            visited[(h - 1) * w + x] = 1

    for y in range(h):
        if is_bg(0, y) and not visited[y * w]:
            queue.append((0, y))
            visited[y * w] = 1
        if is_bg(w - 1, y) and not visited[y * w + (w - 1)]:
            queue.append((w - 1, y))
            visited[y * w + (w - 1)] = 1

    head = 0
    while head < len(queue):
        cx, cy = queue[head]
        head += 1
        out.set_at((cx, cy), (0, 0, 0, 0))
        for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if 0 <= nx < w and 0 <= ny < h:
                idx = ny * w + nx
                if not visited[idx]:
                    visited[idx] = 1
                    if is_bg(nx, ny):
                        queue.append((nx, ny))

    return out


def load_map_png_asset(
    rel_path: str,
    target_size: Optional[Tuple[int, int]] = None,
    colorkey: Optional[Tuple[int, int, int]] = (255, 255, 255),
    flood_fill_outside: bool = True,
) -> Optional[pygame.Surface]:
    """
    Загружает PNG-ассет из папки assets/map/<rel_path>.
    Если flood_fill_outside=True, удаляет белый фон только снаружи контура через flood-fill,
    сохраняя внутренние белые детали нетронутыми.
    Масштабирует через pygame.transform.scale без размытия.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, "assets", "map", *rel_path.split("/"))
    if not os.path.exists(full_path):
        return None
    try:
        surf = pygame.image.load(full_path)
        if flood_fill_outside and colorkey is not None:
            corner = surf.get_at((0, 0))
            if (abs(corner[0] - colorkey[0]) <= 15 and
                abs(corner[1] - colorkey[1]) <= 15 and
                abs(corner[2] - colorkey[2]) <= 15):
                surf = make_outside_transparent(surf, colorkey)
        elif colorkey is not None:
            ck = surf.get_colorkey()
            surf.set_colorkey(colorkey or ck)
            alpha_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            alpha_surf.blit(surf, (0, 0))
            surf = alpha_surf
        if pygame.display.get_surface() is not None:
            surf = surf.convert_alpha()
        if target_size is not None:
            surf = pygame.transform.scale(surf, target_size)
        return surf
    except Exception as e:
        print(f"[ASSET WARNING] Ошибка загрузки {rel_path}: {e}")
        return None


def _build_camp_animation_frames() -> None:
    """Собирает 6 анимированных кадров командного лагеря 96x96 (палатки, баррикада, флаг, костёр)."""
    global _tile_cache
    t_main = load_map_png_asset("2 Objects/8 Camp/2.png", (46, 64), flood_fill_outside=True)
    t_side = load_map_png_asset("2 Objects/8 Camp/1.png", (50, 32), flood_fill_outside=True)
    fence = load_map_png_asset("2 Objects/2 Fence/1.png", (24, 18), flood_fill_outside=True)
    pit = load_map_png_asset("2 Objects/8 Camp/5.png", (28, 18), flood_fill_outside=True)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    flag_path = os.path.join(base_dir, "assets", "map", "3 Animated Objects", "1 Flag", "1.png")
    fire_path = os.path.join(base_dir, "assets", "map", "3 Animated Objects", "2 Campfire", "2.png")

    if not (os.path.exists(flag_path) and os.path.exists(fire_path) and t_main is not None):
        return

    try:
        flag_sheet = make_outside_transparent(pygame.image.load(flag_path))
        fire_sheet = make_outside_transparent(pygame.image.load(fire_path))

        camp_frames = []
        for f in range(6):
            surf = pygame.Surface((96, 96), pygame.SRCALPHA)
            # Флаг (32x64) -> scale to (22, 42)
            fl_sub = flag_sheet.subsurface((f * 32, 0, 32, 64))
            fl = pygame.transform.scale(fl_sub, (22, 42))
            surf.blit(fl, (6, 6))

            # Главный павильон штаба
            surf.blit(t_main, (30, 4))

            # Боковая палатка
            if t_side:
                surf.blit(t_side, (44, 52))

            # Деревянная ограда-баррикада
            if fence:
                surf.blit(fence, (4, 56))

            # Костровище и пламя
            if pit:
                surf.blit(pit, (18, 68))
            fi_sub = fire_sheet.subsurface((f * 32, 0, 32, 32))
            fi = pygame.transform.scale(fi_sub, (22, 22))
            surf.blit(fi, (21, 55))

            camp_frames.append(_safe_convert(surf))

        _tile_cache["camp_frames"] = camp_frames
    except Exception as e:
        print(f"[ASSET WARNING] Не удалось собрать кадры лагеря: {e}")


def init_assets() -> None:
    """Инициализирует кэш процедурных тайлов, диорамы и иконок с безопасным fallback."""
    global _tile_cache, _icon_cache

    for v in range(4):
        _tile_cache[f"grass_{v}"] = _safe_convert(_create_organic_grass_tile(v))

    _tile_cache["build_spot"] = _safe_convert(_create_build_spot_tile())

    # Река (прямая и бесшовные изгибы)
    _tile_cache["river_straight_0"] = _safe_convert(_create_river_tile('straight', 0))
    _tile_cache["river_straight_1"] = _safe_convert(_create_river_tile('straight', 1))
    for bend in ('n_w', 'e_s', 'n_e', 'w_s'):
        _tile_cache[f"river_{bend}"] = _safe_convert(_create_river_tile(bend))
    _tile_cache["bridge"] = _safe_convert(_create_bridge_tile())

    # Дороги процедурные
    for style in ('c_se', 'c_sw', 'c_ne', 'c_nw'):
        _tile_cache[f"road_{style}"] = _safe_convert(_create_road_segment(style))
    for v in range(3):
        _tile_cache[f"road_h_{v}"] = _safe_convert(_create_road_segment('h', v))
        _tile_cache[f"road_v_{v}"] = _safe_convert(_create_road_segment('v', v))

    # Препятствия и декорации
    _tile_cache["obstacle_0"] = _safe_convert(_create_grand_tree_obstacle())
    _tile_cache["obstacle_1"] = _safe_convert(_create_rock_obstacle())
    _tile_cache["obstacle_2"] = _safe_convert(_create_stump_obstacle())
    _tile_cache["obstacle_3"] = _safe_convert(_create_pine_obstacle())
    _tile_cache["prop_signpost"] = _safe_convert(_create_signpost_prop())

    # 3x3 Цитадель Замка (72x72 px) и 2x2 Портал (48x48 px)
    _tile_cache["castle_3x3"] = _safe_convert(_create_castle_3x3())
    _tile_cache["castle_2x2"] = _tile_cache["castle_3x3"]
    _tile_cache["portal_2x2"] = _safe_convert(_create_portal_2x2())

    # Боковые лесные полосы
    _tile_cache["forest_border"] = _safe_convert(_create_side_forest_strip(max(8, MAP_OFFSET_X), MAP_HEIGHT))

    # -------------------------------------------------------------
    # Подключение внешних PNG-ассетов из assets/map/ с fallback
    # -------------------------------------------------------------
    # 1. Трава и автотайлинг дороги из 1 Tiles/
    grass_base = load_map_png_asset("1 Tiles/FieldsTile_38.png", (TILE_SIZE, TILE_SIZE), flood_fill_outside=False)
    if grass_base is not None:
        _tile_cache["grass_0"] = grass_base
        for v in range(1, 4):
            _tile_cache[f"grass_{v}"] = grass_base.copy()

    _tile_cache["wide_bridge"] = _safe_convert(_create_wide_bridge_tile())

    road_mapping = {
        # Сплошная земля (центр широкой дороги) и её вариации
        "road_dirt": "1 Tiles/FieldsTile_01.png",
        "road_dirt_0": "1 Tiles/FieldsTile_01.png",
        "road_dirt_1": "1 Tiles/FieldsTile_18.png",
        "road_dirt_2": "1 Tiles/FieldsTile_20.png",
        "road_dirt_3": "1 Tiles/FieldsTile_27.png",
        "road_cross": "1 Tiles/FieldsTile_01.png",
        # Прямые края с травой (север, юг, запад, восток)
        "road_edge_n_0": "1 Tiles/FieldsTile_34.png",
        "road_edge_n_1": "1 Tiles/FieldsTile_35.png",
        "road_edge_n_2": "1 Tiles/FieldsTile_36.png",
        "road_edge_s_0": "1 Tiles/FieldsTile_02.png",
        "road_edge_s_1": "1 Tiles/FieldsTile_03.png",
        "road_edge_s_2": "1 Tiles/FieldsTile_04.png",
        "road_edge_w_0": "1 Tiles/FieldsTile_13.png",
        "road_edge_w_1": "1 Tiles/FieldsTile_21.png",
        "road_edge_w_2": "1 Tiles/FieldsTile_29.png",
        "road_edge_e_0": "1 Tiles/FieldsTile_09.png",
        "road_edge_e_1": "1 Tiles/FieldsTile_17.png",
        "road_edge_e_2": "1 Tiles/FieldsTile_25.png",
        # Внешние углы (трава с 2 смежных сторон)
        "road_c_se": "1 Tiles/FieldsTile_10.png",
        "road_c_se_1": "1 Tiles/FieldsTile_06.png",
        "road_c_sw": "1 Tiles/FieldsTile_12.png",
        "road_c_sw_1": "1 Tiles/FieldsTile_08.png",
        "road_c_ne": "1 Tiles/FieldsTile_26.png",
        "road_c_ne_1": "1 Tiles/FieldsTile_22.png",
        "road_c_nw": "1 Tiles/FieldsTile_28.png",
        "road_c_nw_1": "1 Tiles/FieldsTile_24.png",
        # Внутренние вогнутые углы (соседи 4 сторон — дорога, диагональный угол — трава)
        "road_in_nw": "1 Tiles/FieldsTile_37.png",
        "road_in_ne": "1 Tiles/FieldsTile_33.png",
        "road_in_sw": "1 Tiles/FieldsTile_05.png",
        "road_in_se_base": "1 Tiles/FieldsTile_11.png",
        "road_in_nw_ne": "1 Tiles/FieldsTile_07.png",
        "road_in_nw_sw": "1 Tiles/FieldsTile_14.png",
        "road_in_nw_se": "1 Tiles/FieldsTile_46.png",
        "road_in_ne_sw": "1 Tiles/FieldsTile_45.png",
        "road_in_ne_se": "1 Tiles/FieldsTile_16.png",
        "road_in_sw_se": "1 Tiles/FieldsTile_23.png",
        "road_in_ne_sw_se": "1 Tiles/FieldsTile_57.png",
        "road_in_nw_sw_se": "1 Tiles/FieldsTile_58.png",
        "road_in_nw_ne_sw": "1 Tiles/FieldsTile_59.png",
        "road_in_nw_ne_se": "1 Tiles/FieldsTile_60.png",
        "road_in_all": "1 Tiles/FieldsTile_15.png",
        # 1-тайловые каналы и тупики (запасные для автотайлинга)
        "road_h": "1 Tiles/FieldsTile_30.png",
        "road_h_1": "1 Tiles/FieldsTile_31.png",
        "road_h_2": "1 Tiles/FieldsTile_39.png",
        "road_v": "1 Tiles/FieldsTile_32.png",
        "road_v_1": "1 Tiles/FieldsTile_40.png",
        "road_v_2": "1 Tiles/FieldsTile_48.png",
        "road_cap_w": "1 Tiles/FieldsTile_41.png",
        "road_cap_e": "1 Tiles/FieldsTile_42.png",
        "road_cap_n": "1 Tiles/FieldsTile_43.png",
        "road_cap_s": "1 Tiles/FieldsTile_44.png",
        "road_iso": "1 Tiles/FieldsTile_47.png",
    }
    for r_key, r_file in road_mapping.items():
        r_surf = load_map_png_asset(r_file, (TILE_SIZE, TILE_SIZE), flood_fill_outside=False)
        if r_surf is not None:
            _tile_cache[r_key] = r_surf
    # Синтез чистого внутреннего юго-восточного угла (in_se) из базы 11 + SE-квадранта тайла 23
    base_se = _tile_cache.get("road_in_se_base") or _tile_cache.get("road_dirt")
    src_se = _tile_cache.get("road_in_sw_se")
    if base_se is not None and src_se is not None:
        half = TILE_SIZE // 2
        in_se = base_se.copy()
        in_se.blit(src_se, (half, half), (half, half, TILE_SIZE - half, TILE_SIZE - half))
        _tile_cache["road_in_se"] = _safe_convert(in_se)

    # 2. Площадка под башни: PlaceForTower1 (38x30 px под масштаб башен 1280x720)
    spot_png = load_map_png_asset("2 Objects/PlaceForTower1.png", (38, 30), flood_fill_outside=True)
    if spot_png is not None:
        _tile_cache["build_spot"] = spot_png

    # 3. Препятствия (деревья, валуны, брёвна, кусты)
    tree1_png = load_map_png_asset("2 Objects/7 Decor/Tree1.png", (38, 48), flood_fill_outside=True)
    if tree1_png is not None:
        _tile_cache["obstacle_0"] = tree1_png

    stone_png = load_map_png_asset("2 Objects/4 Stone/11.png", (30, 30), flood_fill_outside=True)
    if stone_png is not None:
        _tile_cache["obstacle_1"] = stone_png

    log_png = load_map_png_asset("2 Objects/7 Decor/Log1.png", (30, 22), flood_fill_outside=True)
    if log_png is not None:
        log_surf = pygame.Surface((30, 28), pygame.SRCALPHA)
        log_surf.blit(log_png, (0, 4))
        _tile_cache["obstacle_2"] = _safe_convert(log_surf)

    # obstacle_3: куст из 9 Bush/2.png
    bush_png = load_map_png_asset("2 Objects/9 Bush/2.png", (32, 26), flood_fill_outside=True)
    if bush_png is not None:
        bush_surf = pygame.Surface((32, 28), pygame.SRCALPHA)
        bush_surf.blit(bush_png, (0, 2))
        _tile_cache["obstacle_3"] = _safe_convert(bush_surf)

    # Декоративный указатель
    sign_png = load_map_png_asset("2 Objects/3 Pointer/1.png", (20, 28), flood_fill_outside=True)
    if sign_png is not None:
        sign_surf = pygame.Surface((26, 28), pygame.SRCALPHA)
        sign_surf.blit(sign_png, (3, 0))
        _tile_cache["prop_signpost"] = _safe_convert(sign_surf)

    # Украшения луга (трава и цветы)
    grass_prop = load_map_png_asset("2 Objects/5 Grass/1.png", flood_fill_outside=True)
    flower1_prop = load_map_png_asset("2 Objects/6 Flower/1.png", flood_fill_outside=True)
    flower2_prop = load_map_png_asset("2 Objects/6 Flower/2.png", flood_fill_outside=True)
    if grass_prop is not None:
        s1 = _tile_cache["grass_1"].copy()
        s1.blit(grass_prop, (8, 9))
        _tile_cache["grass_1"] = _safe_convert(s1)
    if flower1_prop is not None:
        s2 = _tile_cache["grass_2"].copy()
        s2.blit(flower1_prop, (10, 10))
        _tile_cache["grass_2"] = _safe_convert(s2)
    if flower2_prop is not None:
        s3 = _tile_cache["grass_3"].copy()
        s3.blit(flower2_prop, (12, 8))
        _tile_cache["grass_3"] = _safe_convert(s3)

    # 4. Командный лагерь из 8 Camp/ + анимированный костёр + знамёна
    _build_camp_animation_frames()

    # Объёмные иконки HUD (масштаб под 1280x720)
    _icon_cache = {
        "heart_3d": _safe_convert(pygame.transform.scale(_create_icon_heart_3d(), (24, 24))),
        "coin_3d": _safe_convert(pygame.transform.scale(_create_icon_coin_3d(), (24, 24))),
        "skull_3d": _safe_convert(pygame.transform.scale(_create_icon_skull_3d(), (22, 22))),
        "sound": _safe_convert(pygame.transform.scale(_create_icon_sound_3d(), (26, 26))),
        "pause": _safe_convert(pygame.transform.scale(_create_icon_pause_3d(), (26, 26))),
        "fast_forward": _safe_convert(pygame.transform.scale(_create_icon_fast_forward_3d(), (26, 26))),
    }

    # 5. Загрузка PNG-ассетов командиров (Рыцарь-командир и иконки навыков)
    _load_hero_assets()

    # 6. Загрузка PNG-ассетов башен (Башня лучников и Башня магов)
    _load_all_tower_packs()

    # 7. Загрузка PNG-ассетов врагов (Слизень, Гоблин, Волк, Пчела)
    _load_all_enemy_packs()


def _load_hero_png(rel_path: str) -> Optional[pygame.Surface]:
    """Загружает PNG-ассет героя из папки assets/heroes/ через .convert_alpha()."""
    full_path = os.path.join("assets", "heroes", rel_path)
    if not os.path.exists(full_path):
        return None
    try:
        return _safe_convert(pygame.image.load(full_path))
    except Exception:
        return None


def _slice_spritesheet(sheet: Optional[pygame.Surface], frame_w: int = 32, frame_h: int = 32) -> List[pygame.Surface]:
    """Нарезает горизонтальный спрайт-лист на отдельные кадры frame_w x frame_h."""
    if sheet is None:
        return [_safe_convert(pygame.Surface((frame_w, frame_h), pygame.SRCALPHA))]
    sw, sh = sheet.get_size()
    count = max(1, sw // max(1, frame_w))
    frames: List[pygame.Surface] = []
    for i in range(count):
        frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), pygame.Rect(i * frame_w, 0, frame_w, min(frame_h, sh)))
        frames.append(_safe_convert(frame))
    return frames


def _slice_square_strip(sheet: Optional[pygame.Surface]) -> List[pygame.Surface]:
    """Определяет квадратный размер кадра полосы по её высоте и нарезает кадры."""
    if sheet is None:
        return []
    sw, sh = sheet.get_size()
    if sw <= 0 or sh <= 0:
        return []
    cell = sh if sw >= sh else sw
    return _slice_spritesheet(sheet, cell, sh)


def _crop_and_scale_hero_anims(
    raw_anims: Dict[str, List[pygame.Surface]],
    target_fig_h: float = 40.0,
) -> Tuple[Dict[str, List[pygame.Surface]], Dict[str, object], pygame.Surface]:
    """
    Вычисляет единый симметричный bounding box относительно центра и линии ног
    по всем анимациям (Idle, Run, Attack1, Attack2, Guard), обрезает пустые поля,
    масштабирует без размытия под высоту ~34-42 px и вырезает крупный бюст-портрет.
    """
    idle_frames = raw_anims.get("idle", [])
    sample = idle_frames[0] if idle_frames else _safe_convert(pygame.Surface((32, 32), pygame.SRCALPHA))
    cell_w, cell_h = sample.get_size()
    cx = cell_w // 2

    idle_tops: List[int] = []
    idle_bottoms: List[int] = []
    min_top = cell_h
    max_bot = 0
    left_reach = 8
    right_reach = 8

    for key, frames in raw_anims.items():
        for frame in frames:
            b = frame.get_bounding_rect(min_alpha=10)
            if b.w <= 0 or b.h <= 0:
                continue
            min_top = min(min_top, b.top)
            max_bot = max(max_bot, b.bottom)
            left_reach = max(left_reach, cx - b.left)
            right_reach = max(right_reach, b.right - cx)
            if key == "idle":
                idle_tops.append(b.top)
                idle_bottoms.append(b.bottom)

    if max_bot <= min_top:
        min_top, max_bot = 0, cell_h
    foot_y = sorted(idle_bottoms)[len(idle_bottoms) // 2] if idle_bottoms else max_bot
    idle_min_top = min(idle_tops) if idle_tops else min_top
    idle_fig_h = max(1, foot_y - idle_min_top)

    half_w = min(cx, cell_w - cx, max(left_reach, right_reach) + 2)
    crop_x = cx - half_w
    crop_w = max(2, half_w * 2)
    crop_y = max(0, min_top - 2)
    crop_bot = min(cell_h, max_bot + 2)
    crop_h = max(2, crop_bot - crop_y)
    crop_rect = pygame.Rect(crop_x, crop_y, crop_w, crop_h)

    scale = target_fig_h / float(idle_fig_h)
    draw_w = max(24, int(round((crop_w * scale) / 2.0)) * 2)
    draw_h = max(24, int(round(crop_h * scale)))
    foot_ratio = max(0.5, min(0.95, (foot_y - crop_y) / float(crop_h)))

    scaled_anims: Dict[str, List[pygame.Surface]] = {}
    for key, frames in raw_anims.items():
        out_frames: List[pygame.Surface] = []
        for frame in frames:
            cropped = pygame.Surface((crop_w, crop_h), pygame.SRCALPHA)
            cropped.blit(frame, (0, 0), crop_rect)
            scaled = _safe_convert(pygame.transform.scale(cropped, (draw_w, draw_h)))
            out_frames.append(scaled)
        scaled_anims[key] = out_frames

    # Портрет-бюст из первого кадра Warrior_Idle (верхняя часть + шлем + щит)
    f0 = idle_frames[0] if idle_frames else sample
    b0 = f0.get_bounding_rect(min_alpha=10)
    if cell_w >= 64 and b0.w > 0 and b0.h > 0:
        side = min(cell_w, cell_h, max(48, int(round(b0.h * 0.85))))
        px = max(0, min(cell_w - side, b0.x - 6))
        py = max(0, min(cell_h - side, b0.y - 6))
        portrait = pygame.Surface((side, side), pygame.SRCALPHA)
        portrait.blit(f0, (0, 0), pygame.Rect(px, py, side, side))
        portrait = _safe_convert(portrait)
    else:
        portrait = scaled_anims["idle"][0] if scaled_anims.get("idle") else sample

    meta = {"draw_size": (draw_w, draw_h), "foot_ratio": foot_ratio, "crop_size": (crop_w, crop_h)}
    return scaled_anims, meta, portrait


def _load_hero_assets() -> None:
    """Загружает нарезанные анимации, метрики привязки и портрет Рыцаря Tiny Swords."""
    global _hero_anim_cache, _hero_portrait_cache, _hero_meta_cache
    _hero_anim_cache = {}
    _hero_portrait_cache = {}
    _hero_meta_cache = {}

    # Рыцарь-командир (Tiny Swords PNG-полосы 192x192 в assets/heroes/knight/)
    idle_sheet = _load_hero_png("knight/Warrior_Idle.png") or _load_hero_png("knight/knight_idle.png")
    walk_sheet = _load_hero_png("knight/Warrior_Run.png") or _load_hero_png("knight/knight_walk.png")
    atk1_sheet = _load_hero_png("knight/Warrior_Attack1.png") or _load_hero_png("knight/knight_attack.png")
    atk2_sheet = _load_hero_png("knight/Warrior_Attack2.png")
    guard_sheet = _load_hero_png("knight/Warrior_Guard.png")

    raw_anims: Dict[str, List[pygame.Surface]] = {
        "idle": _slice_square_strip(idle_sheet),
        "walk": _slice_square_strip(walk_sheet),
        "attack1": _slice_square_strip(atk1_sheet),
    }
    if atk2_sheet is not None:
        raw_anims["attack2"] = _slice_square_strip(atk2_sheet)
    else:
        raw_anims["attack2"] = raw_anims["attack1"]
    if guard_sheet is not None:
        raw_anims["guard"] = _slice_square_strip(guard_sheet)

    scaled_anims, meta, portrait = _crop_and_scale_hero_anims(raw_anims, target_fig_h=40.0)
    scaled_anims["attack"] = scaled_anims.get("attack1", [])

    _hero_anim_cache["knight"] = scaled_anims
    _hero_meta_cache["knight"] = meta

    explicit_portrait = _load_hero_png("knight/knight_portrait.png")
    final_portrait = explicit_portrait if explicit_portrait is not None else portrait
    _hero_portrait_cache["knight"] = final_portrait

    # Иконка портрета Рыцаря для медальона [C] в HUD (42x42 внутри кнопки)
    hud_portrait = _safe_convert(pygame.transform.scale(final_portrait, (42, 42)))
    _icon_cache["hero_card_3d"] = hud_portrait
    _icon_cache["knight_card_3d"] = hud_portrait


def get_grass_tile(variant: int = 0) -> pygame.Surface:
    if not _tile_cache:
        init_assets()
    return _tile_cache.get(f"grass_{variant % 4}", _tile_cache["grass_0"])


def get_build_spot_tile() -> pygame.Surface:
    if not _tile_cache:
        init_assets()
    return _tile_cache["build_spot"]


def get_river_tile(flow_type: str = 'straight', variant: int = 0) -> pygame.Surface:
    if not _tile_cache:
        init_assets()
    if flow_type == 'straight':
        key = f"river_straight_{variant % 2}"
    else:
        key = f"river_{flow_type}"
    return _tile_cache.get(key, _tile_cache["river_straight_0"])


def get_bridge_tile() -> pygame.Surface:
    if not _tile_cache:
        init_assets()
    return _tile_cache["bridge"]


def get_road_segment(style: str, variant: int = 0) -> pygame.Surface:
    if not _tile_cache:
        init_assets()
    if style in ('h', 'v'):
        key = f"road_{style}_{variant % 3}"
    else:
        key = f"road_{style}"
    return _tile_cache.get(key, _tile_cache.get("road_h_0", _tile_cache["road_c_se"]))


def get_road_tile(style: str) -> pygame.Surface:
    """Возвращает тайл дороги из пака 1 Tiles/ по стилю автотайлинга ('h', 'v', 'c_se', etc.)."""
    if not _tile_cache:
        init_assets()
    key = f"road_{style}"
    if key in _tile_cache:
        return _tile_cache[key]
    if "road_dirt" in _tile_cache:
        return _tile_cache["road_dirt"]
    return get_road_segment(style)


def get_road_surface(road_nodes: list) -> pygame.Surface:
    """Возвращает кэшированный цельный слой дороги на весь экран в стиле Kingdom Rush."""
    if not _tile_cache:
        init_assets()
    if "road_continuous" not in _tile_cache:
        _tile_cache["road_continuous"] = _safe_convert(create_continuous_road_surface(road_nodes))
    return _tile_cache["road_continuous"]


def get_obstacle_tile(variant: int = 0) -> pygame.Surface:
    if not _tile_cache:
        init_assets()
    return _tile_cache.get(f"obstacle_{variant % 4}", _tile_cache["obstacle_0"])


def get_bush_tile(variant: int = 0) -> pygame.Surface:
    """Возвращает спрайт куста из 9 Bush/."""
    if not _tile_cache:
        init_assets()
    return _tile_cache.get("obstacle_3", _tile_cache["obstacle_0"])


def get_signpost_tile() -> pygame.Surface:
    if not _tile_cache:
        init_assets()
    return _tile_cache["prop_signpost"]


def get_castle_3x3(anim_time: float = 0.0) -> pygame.Surface:
    """Возвращает анимированный командный лагерь (или процедурный замок как fallback)."""
    if not _tile_cache:
        init_assets()
    if "camp_frames" in _tile_cache and _tile_cache["camp_frames"]:
        frames = _tile_cache["camp_frames"]
        idx = int(anim_time * 8.0) % len(frames)
        return frames[idx]
    return _tile_cache.get("castle_3x3", _tile_cache["build_spot"])


def get_castle_2x2() -> pygame.Surface:
    return get_castle_3x3()


def get_portal_2x2() -> pygame.Surface:
    if not _tile_cache:
        init_assets()
    return _tile_cache["portal_2x2"]


def get_forest_border() -> pygame.Surface:
    if not _tile_cache:
        init_assets()
    return _tile_cache["forest_border"]


def get_hud_icon(name: str) -> pygame.Surface:
    if not _icon_cache:
        init_assets()
    return _icon_cache.get(name, _icon_cache["heart_3d"])


def get_hero_animations(hero_id: str = "knight") -> Dict[str, List[pygame.Surface]]:
    """Возвращает словарь кадров анимации {'idle', 'walk', 'attack', 'attack1', 'attack2', 'guard'} для командира."""
    if not _hero_anim_cache:
        init_assets()
    return _hero_anim_cache.get(hero_id, _hero_anim_cache.get("knight", {}))


def get_hero_portrait(hero_id: str = "knight") -> pygame.Surface:
    """Возвращает крупный бюст-портрет командира для HUD [C], карточки и экрана выбора."""
    if not _hero_portrait_cache:
        init_assets()
    return _hero_portrait_cache.get(hero_id, _icon_cache["heart_3d"])


def get_hero_draw_metrics(hero_id: str = "knight") -> Dict[str, object]:
    """Возвращает размер отрисовки и нормализованную точку опоры ног командира."""
    if not _hero_meta_cache:
        init_assets()
    return _hero_meta_cache.get(hero_id, _hero_meta_cache.get("knight", {"draw_size": (62, 52), "foot_ratio": 0.82}))


_ENEMY_SCALE_FACTORS: Dict[str, float] = {
    "slime": 1.18,
    "bee": 1.18,
    "wolf": 1.25,
    "goblin": 1.30,
}


def _find_enemy_pack_dir(enemy_type: str) -> Optional[str]:
    """Находит папку с PNG-листами врага (включая вложенные подпапки 1/, 2/, 3/, 4/)."""
    base = os.path.join("assets", "enemies", enemy_type)
    if not os.path.isdir(base):
        return None
    if os.path.exists(os.path.join(base, "S_Walk.png")) or os.path.exists(os.path.join(base, "D_Walk.png")):
        return base
    for sub in sorted(os.listdir(base)):
        sub_path = os.path.join(base, sub)
        if os.path.isdir(sub_path) and (
            os.path.exists(os.path.join(sub_path, "S_Walk.png"))
            or os.path.exists(os.path.join(sub_path, "D_Walk.png"))
        ):
            return sub_path
    return None


def _compute_enemy_crop_metrics(
    raw_dirs: Dict[str, Dict[str, List[pygame.Surface]]]
) -> Tuple[pygame.Rect, float, float]:
    """Вычисляет симметричный crop вокруг (cx, foot_y) и относительные верх/низ фигуры."""
    sample = None
    for anim_map in raw_dirs.values():
        for frames in anim_map.values():
            if frames:
                sample = frames[0]
                break
        if sample is not None:
            break
    if sample is None:
        return pygame.Rect(0, 0, 48, 48), 0.1, 0.85

    cell_w, cell_h = sample.get_size()
    cx = cell_w // 2
    min_top, max_bot = cell_h, 0
    left_reach, right_reach = 6, 6
    walk_tops: List[int] = []
    walk_bottoms: List[int] = []

    for anim_key, anim_map in raw_dirs.items():
        for frames in anim_map.values():
            for frame in frames:
                b = frame.get_bounding_rect(min_alpha=10)
                if b.w <= 0 or b.h <= 0:
                    continue
                min_top = min(min_top, b.top)
                max_bot = max(max_bot, b.bottom)
                left_reach = max(left_reach, cx - b.left)
                right_reach = max(right_reach, b.right - cx)
                if anim_key == "walk":
                    walk_tops.append(b.top)
                    walk_bottoms.append(b.bottom)

    if max_bot <= min_top:
        min_top, max_bot = 0, cell_h
    foot_y = sorted(walk_bottoms)[len(walk_bottoms) // 2] if walk_bottoms else max_bot
    walk_top = sorted(walk_tops)[len(walk_tops) // 2] if walk_tops else min_top

    half_w = min(cx, cell_w - cx, max(left_reach, right_reach) + 2)
    crop_x = cx - half_w
    crop_w = max(2, half_w * 2)
    crop_y = max(0, min_top - 2)
    crop_bot = min(cell_h, max_bot + 2)
    crop_h = max(2, crop_bot - crop_y)

    head_ratio = max(0.02, min(0.5, (walk_top - crop_y) / float(crop_h)))
    foot_ratio = max(0.5, min(0.96, (foot_y - crop_y) / float(crop_h)))
    return pygame.Rect(crop_x, crop_y, crop_w, crop_h), head_ratio, foot_ratio


def _scale_enemy_pack(
    raw_dirs: Dict[str, Dict[str, List[pygame.Surface]]],
    crop_rect: pygame.Rect,
    scale_factor: float,
    head_ratio: float,
    foot_ratio: float,
    has_native_attack: bool,
) -> Tuple[Dict[str, Dict[str, List[pygame.Surface]]], Dict[str, object]]:
    """Обрезает и масштабирует кадры врага через pygame.transform.scale без размытия."""
    draw_w = max(18, int(round((crop_rect.w * scale_factor) / 2.0)) * 2)
    draw_h = max(18, int(round(crop_rect.h * scale_factor)))
    scaled: Dict[str, Dict[str, List[pygame.Surface]]] = {}
    for anim_key, dir_map in raw_dirs.items():
        scaled_dirs: Dict[str, List[pygame.Surface]] = {}
        for dir_key, frames in dir_map.items():
            out: List[pygame.Surface] = []
            for frame in frames:
                cropped = pygame.Surface((crop_rect.w, crop_rect.h), pygame.SRCALPHA)
                cropped.blit(frame, (0, 0), crop_rect)
                out.append(_safe_convert(pygame.transform.scale(cropped, (draw_w, draw_h))))
            scaled_dirs[dir_key] = out
        scaled[anim_key] = scaled_dirs
    meta: Dict[str, object] = {
        "draw_size": (draw_w, draw_h),
        "head_ratio": head_ratio,
        "foot_ratio": foot_ratio,
        "has_native_attack": has_native_attack,
    }
    return scaled, meta


def _load_all_enemy_packs() -> None:
    """Сканирует assets/enemies/ и кэширует PNG-анимации (D/S/U Walk/Attack/Death) для 4 врагов."""
    global _enemy_anim_cache, _enemy_meta_cache
    _enemy_anim_cache = {}
    _enemy_meta_cache = {}

    for enemy_type, base_scale in _ENEMY_SCALE_FACTORS.items():
        pack_dir = _find_enemy_pack_dir(enemy_type)
        raw_dirs: Dict[str, Dict[str, List[pygame.Surface]]] = {
            "walk": {},
            "attack": {},
            "death": {},
        }
        has_native_attack = False

        if pack_dir is not None:
            for d_key in ("D", "S", "U"):
                walk_path = os.path.join(pack_dir, f"{d_key}_Walk.png")
                walk_frames = (
                    _slice_square_strip(_safe_convert(pygame.image.load(walk_path)))
                    if os.path.exists(walk_path)
                    else [_safe_convert(pygame.Surface((48, 48), pygame.SRCALPHA))]
                )
                raw_dirs["walk"][d_key] = walk_frames

                atk_path = os.path.join(pack_dir, f"{d_key}_Attack.png")
                if os.path.exists(atk_path):
                    has_native_attack = True
                    raw_dirs["attack"][d_key] = _slice_square_strip(_safe_convert(pygame.image.load(atk_path)))
                else:
                    raw_dirs["attack"][d_key] = list(walk_frames)

                death_path = os.path.join(pack_dir, f"{d_key}_Death.png")
                if os.path.exists(death_path):
                    raw_dirs["death"][d_key] = _slice_square_strip(_safe_convert(pygame.image.load(death_path)))
                else:
                    raw_dirs["death"][d_key] = list(walk_frames)
        else:
            fallback = [_safe_convert(pygame.Surface((48, 48), pygame.SRCALPHA))]
            for a_key in ("walk", "attack", "death"):
                for d_key in ("D", "S", "U"):
                    raw_dirs[a_key][d_key] = list(fallback)

        crop_rect, head_ratio, foot_ratio = _compute_enemy_crop_metrics(raw_dirs)
        for is_boss, scale_mult in ((False, 1.0), (True, 1.25)):
            anims, meta = _scale_enemy_pack(
                raw_dirs, crop_rect, base_scale * scale_mult, head_ratio, foot_ratio, has_native_attack
            )
            _enemy_anim_cache[(enemy_type, is_boss)] = anims
            _enemy_meta_cache[(enemy_type, is_boss)] = meta


def get_enemy_animations(
    enemy_type: str = "slime", is_boss: bool = False
) -> Dict[str, Dict[str, List[pygame.Surface]]]:
    """Возвращает словарь анимаций {'walk'|'attack'|'death' -> {'D'|'S'|'U' -> frames}}."""
    if not _enemy_anim_cache:
        init_assets()
    return _enemy_anim_cache.get(
        (enemy_type, is_boss),
        _enemy_anim_cache.get(("slime", False), {}),
    )


def get_enemy_draw_metrics(enemy_type: str = "slime", is_boss: bool = False) -> Dict[str, object]:
    """Возвращает размер кадра, верх головы и линию опоры врага."""
    if not _enemy_meta_cache:
        init_assets()
    return _enemy_meta_cache.get(
        (enemy_type, is_boss),
        _enemy_meta_cache.get(("slime", False), {"draw_size": (48, 40), "head_ratio": 0.1, "foot_ratio": 0.82, "has_native_attack": False}),
    )


_ROAD_AUTOTILE_VARIANTS: Dict[str, List[str]] = {
    "dirt": ["road_dirt_0", "road_dirt_1", "road_dirt_2", "road_dirt_3"],
    "edge_n": ["road_edge_n_0", "road_edge_n_1", "road_edge_n_2"],
    "edge_s": ["road_edge_s_0", "road_edge_s_1", "road_edge_s_2"],
    "edge_w": ["road_edge_w_0", "road_edge_w_1", "road_edge_w_2"],
    "edge_e": ["road_edge_e_0", "road_edge_e_1", "road_edge_e_2"],
    "c_se": ["road_c_se", "road_c_se_1"],
    "c_sw": ["road_c_sw", "road_c_sw_1"],
    "c_ne": ["road_c_ne", "road_c_ne_1"],
    "c_nw": ["road_c_nw", "road_c_nw_1"],
    "h": ["road_h", "road_h_1", "road_h_2"],
    "v": ["road_v", "road_v_1", "road_v_2"],
}


def get_road_autotile(style: str, variant: int = 0) -> pygame.Surface:
    """Возвращает тайл дороги для 8-направленного автотайлинга с вариацией текстуры."""
    if not _tile_cache:
        init_assets()
    variants = _ROAD_AUTOTILE_VARIANTS.get(style)
    if variants:
        key = variants[variant % len(variants)]
        if key in _tile_cache:
            return _tile_cache[key]
    direct_key = f"road_{style}"
    if direct_key in _tile_cache:
        return _tile_cache[direct_key]
    return get_road_tile(style)


def get_wide_bridge_tile() -> pygame.Surface:
    """Возвращает деревянный мост высотой 3 тайла (24x72 px)."""
    if not _tile_cache:
        init_assets()
    return _tile_cache.get("wide_bridge", _tile_cache["bridge"])


# ==============================================================
# АССЕТЫ БАШЕН: ЛУЧНИКИ И МАГИ (assets/towers/<type>/)
# ==============================================================

ARCHER_TOWER_W = 46
ARCHER_TOWER_H = 85
ARCHER_UNIT_SIZE = 31


def _resolve_tower_asset_path(tower_type: str, rel_path: str) -> Optional[str]:
    """Ищет PNG башни с fallback для '2 Idle/1.png' -> '`.png' у пака магов."""
    base_dir = os.path.join("assets", "towers", tower_type)
    full_path = os.path.join(base_dir, rel_path)
    if os.path.exists(full_path):
        return full_path
    if rel_path == "2 Idle/1.png":
        fallback = os.path.join(base_dir, "2 Idle", chr(96) + ".png")
        if os.path.exists(fallback):
            return fallback
    return None


def _load_tower_sheet_frames(
    tower_type: str,
    rel_path: str,
    frame_w: int,
    frame_h: int,
    target_size: Tuple[int, int],
) -> List[pygame.Surface]:
    """Загружает горизонтальный спрайт-лист башни/юнита без размытия."""
    full_path = _resolve_tower_asset_path(tower_type, rel_path)
    if not full_path:
        return []
    sheet = _safe_convert(pygame.image.load(full_path))
    count = max(1, sheet.get_width() // frame_w)
    frames: List[pygame.Surface] = []
    for i in range(count):
        rect = pygame.Rect(i * frame_w, 0, min(frame_w, sheet.get_width() - i * frame_w), min(frame_h, sheet.get_height()))
        sub = sheet.subsurface(rect).copy()
        c0 = sub.get_at((0, 0))
        if c0[3] == 255 and (c0[:3] == (255, 255, 255) or c0[:3] == (0, 0, 0)):
            sub = make_outside_transparent(sub)
        frames.append(_safe_convert(pygame.transform.scale(sub, target_size)))
    return frames


def _load_tower_pack(tower_type: str) -> Dict[str, object]:
    """Предзагружает уровни 1-7 (2 Idle, 1 Upgrade), юнитов 1-3 и снаряды для типа башни."""
    idle_map: Dict[int, List[pygame.Surface]] = {}
    upg_map: Dict[int, List[pygame.Surface]] = {}
    for lvl in range(1, 8):
        idle_map[lvl] = _load_tower_sheet_frames(tower_type, f"2 Idle/{lvl}.png", 70, 130, (ARCHER_TOWER_W, ARCHER_TOWER_H))
        upg_map[lvl] = _load_tower_sheet_frames(tower_type, f"1 Upgrade/{lvl}.png", 70, 130, (ARCHER_TOWER_W, ARCHER_TOWER_H))

    units_map: Dict[Tuple[int, str, str, bool], List[pygame.Surface]] = {}
    for tier in (1, 2, 3):
        for d_key in ("D", "S", "U"):
            for state in ("Idle", "Preattack", "Attack"):
                base_frames = _load_tower_sheet_frames(
                    tower_type,
                    f"3 Units/{tier}/{d_key}_{state}.png",
                    48,
                    48,
                    (ARCHER_UNIT_SIZE, ARCHER_UNIT_SIZE),
                )
                units_map[(tier, d_key, state, False)] = base_frames
                units_map[(tier, d_key, state, True)] = [
                    _safe_convert(pygame.transform.flip(f, True, False)) for f in base_frames
                ]

    pack: Dict[str, object] = {
        "idle": idle_map,
        "upgrade": upg_map,
        "units": units_map,
    }

    if tower_type == "archer":
        arrow_path = _resolve_tower_asset_path("archer", "3 Units/Arrow/13.png")
        if arrow_path:
            pack["arrow"] = _safe_convert(pygame.image.load(arrow_path))
        else:
            arrow_surf = pygame.Surface((14, 3), pygame.SRCALPHA)
            pygame.draw.line(arrow_surf, (150, 110, 65), (0, 1), (11, 1), 1)
            pygame.draw.line(arrow_surf, (240, 245, 255), (11, 1), (13, 1), 1)
            pack["arrow"] = arrow_surf
    elif tower_type == "mage":
        proj_map: Dict[int, pygame.Surface] = {}
        for p_tier in (1, 2, 3):
            p_path = _resolve_tower_asset_path("mage", f"3 Units/Projectiles/{p_tier}.png")
            if p_path:
                raw_orb = _safe_convert(pygame.image.load(p_path))
                proj_map[p_tier] = _safe_convert(pygame.transform.scale(raw_orb, (8, 8)))
        pack["projectiles"] = proj_map

    return pack


def _load_all_tower_packs() -> None:
    """Загружает ассеты всех доступных башен (лучников и магов)."""
    global _tower_packs_cache
    for t_type in ("archer", "mage"):
        _tower_packs_cache[t_type] = _load_tower_pack(t_type)


def _get_tower_pack(tower_type: str) -> Dict[str, object]:
    if tower_type not in _tower_packs_cache:
        _tower_packs_cache[tower_type] = _load_tower_pack(tower_type)
    return _tower_packs_cache[tower_type]


def get_tower_idle_frames(tower_type: str, level: int) -> List[pygame.Surface]:
    """Возвращает кадры Idle-анимации башни указанного типа (уровни 1-7)."""
    pack = _get_tower_pack(tower_type)
    idle_map = pack["idle"]  # type: ignore[index]
    lvl = max(1, min(7, level))
    return idle_map.get(lvl) or idle_map.get(1) or []


def get_tower_upgrade_frames(tower_type: str, level: int) -> List[pygame.Surface]:
    """Возвращает кадры анимации постройки/апгрейда башни указанного типа (уровни 1-7)."""
    pack = _get_tower_pack(tower_type)
    upg_map = pack["upgrade"]  # type: ignore[index]
    lvl = max(1, min(7, level))
    return upg_map.get(lvl) or upg_map.get(1) or []


def get_tower_unit_frames(
    tower_type: str,
    unit_tier: int,
    dir_key: str,
    state: str,
    flip_x: bool = False,
) -> List[pygame.Surface]:
    """Возвращает кадры юнита на вершине башни (tier 1-3, U/D/S, Idle/Preattack/Attack)."""
    pack = _get_tower_pack(tower_type)
    units_map = pack["units"]  # type: ignore[index]
    tier = max(1, min(3, unit_tier))
    return units_map.get((tier, dir_key, state, flip_x), [])


def get_mage_projectile_sprite(proj_tier: int = 1) -> pygame.Surface:
    """Возвращает PNG-спрайт магического снаряда (1..3) из assets/towers/mage/3 Units/Projectiles/."""
    pack = _get_tower_pack("mage")
    proj_map = pack.get("projectiles", {})  # type: ignore[assignment]
    t = max(1, min(3, proj_tier))
    if t in proj_map:
        return proj_map[t]
    fallback = pygame.Surface((8, 8), pygame.SRCALPHA)
    pygame.draw.circle(fallback, (195, 120, 255), (4, 4), 3)
    return fallback


def get_archer_tower_frames(level: int) -> List[pygame.Surface]:
    return get_tower_idle_frames("archer", level)


def get_archer_upgrade_frames(level: int) -> List[pygame.Surface]:
    return get_tower_upgrade_frames("archer", level)


def get_archer_unit_frames(unit_tier: int, dir_key: str, state: str, flip_x: bool = False) -> List[pygame.Surface]:
    return get_tower_unit_frames("archer", unit_tier, dir_key, state, flip_x)


def get_arrow_sprite() -> pygame.Surface:
    """Возвращает PNG-спрайт летящей стрелы (направлен вправо)."""
    pack = _get_tower_pack("archer")
    return pack["arrow"]  # type: ignore[return-value]
