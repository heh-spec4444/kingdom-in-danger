"""
Модуль карты игрового мира: просторная полноэкранная диорама 52x30 тайлов (1280x720 px).
Включает:
- Бесшовный луг с природными цветочными полянками
- Плавно изгибающуюся реку с 3 деревянными мостами
- Длинную извилистую дорогу от левого края к Командному лагерю справа
- Лесные рощи, валуны, поваленные брёвна, кусты и указатели на свободном пространстве
- Командный лагерь 4x4 (96x96 px) с анимированным костром и флагом
- 9 фиксированных строительных площадок вдоль дороги
"""

import math
from typing import List, Tuple, Optional, Dict
import pygame
from settings import (
    GRID_COLS,
    GRID_ROWS,
    TILE_SIZE,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    TILE_GRASS,
    TILE_ROAD,
    TILE_OBSTACLE,
    TILE_SPAWN,
    TILE_CASTLE,
    TILE_WATER,
    TILE_BRIDGE,
    TILE_BUILD_SPOT,
    TILE_TOWER,
    BUILD_SPOTS_COORDS,
)
from core.assets import (
    get_grass_tile,
    get_river_tile,
    get_bridge_tile,
    get_wide_bridge_tile,
    get_build_spot_tile,
    get_road_autotile,
    get_road_segment,
    get_road_surface,
    get_road_tile,
    get_obstacle_tile,
    get_bush_tile,
    get_signpost_tile,
    get_castle_3x3,
    get_forest_border,
)


def _pseudo_hash(c: int, r: int, seed: float = 42.1) -> int:
    """Генерирует мягкий псевдослучайный шум."""
    return int(abs(math.sin(c * 12.9898 + r * 78.233 + seed) * 43758.5453)) % 1000


class GameMap:
    """Управляет картой-диорамой: изгибы реки, мост, лес, площадки и поиск пути."""

    def __init__(self):
        self.cols = GRID_COLS
        self.rows = GRID_ROWS
        self.tile_size = TILE_SIZE
        self.offset_x = MAP_OFFSET_X
        self.offset_y = MAP_OFFSET_Y

        # Инициализируем всю карту органичной травой
        self.grid = [[TILE_GRASS for _ in range(self.cols)] for _ in range(self.rows)]

        self.grass_variants: Dict[Tuple[int, int], int] = {}
        self.obstacle_variants: Dict[Tuple[int, int], int] = {}
        self.river_data: Dict[Tuple[int, int], str] = {}  # (c, r) -> 'straight', 'turn_w', 'turn_e'

        # Контрольные точки извилистой 3-тайловой дороги в сетке 40x30 (960x720 -> 1440x1080)
        self.road_nodes = [
            (0, 7),    # Выход врагов с левого края экрана
            (6, 7),    # Короткий прямой участок у заставы
            (6, 4),    # Подъём на северный тракт
            (25, 4),   # Пересечение 1-го моста на (20, 4)
            (25, 11),  # Спуск к центральной переправе
            (10, 11),  # Пересечение 2-го моста на (19, 11)
            (10, 23),  # Длинный спуск в южные луга
            (29, 23),  # Пересечение 3-го моста на (21, 23)
            (29, 16),  # Подъём к лагерю
            (37, 16),  # Вход прямо к воротам Командного лагеря
        ]
        self.bridge_coords = [(20, 4), (19, 11), (21, 23)]

        self._init_variants()
        self._carve_curved_river()
        self._carve_road()
        self._place_build_spots()
        self._place_fortresses()
        self._place_forests_and_props()
        self.anim_time: float = 0.0

    def update(self, dt: float) -> None:
        """Обновляет анимационные таймеры карты (костёр, знамёна лагеря)."""
        self.anim_time += dt

    def _init_variants(self) -> None:
        """Создаёт мягкие природные пятна травы на едином базовом фоне."""
        for r in range(self.rows):
            for c in range(self.cols):
                h = _pseudo_hash(c, r, 55.4)
                if h < 600:
                    v = 0  # чистый луг (60%)
                elif h < 780:
                    v = 1  # клевер (18%)
                elif h < 890:
                    v = 2  # редкие полевые цветы (11%)
                else:
                    v = 3  # мягкий мох (11%)
                self.grass_variants[(c, r)] = v

    def _carve_curved_river(self) -> None:
        """Прокладывает плавно изгибающуюся реку через карту 40x30 с 3 мостами."""
        river_tiles = []
        # r=0..7: колонка 20 (через 1-й мост на (20, 4))
        for r in range(0, 8):
            river_tiles.append((20, r, 'straight'))
        # r=8: изгиб влево в колонку 19
        river_tiles.append((20, 8, 'n_w'))
        river_tiles.append((19, 8, 'e_s'))
        # r=9..15: колонка 19 (через 2-й мост на (19, 11))
        for r in range(9, 16):
            river_tiles.append((19, r, 'straight'))
        # r=16: изгиб вправо в колонку 20
        river_tiles.append((19, 16, 'n_e'))
        river_tiles.append((20, 16, 'w_s'))
        # r=17..18: колонка 20
        for r in range(17, 19):
            river_tiles.append((20, r, 'straight'))
        # r=19: плавный изгиб вправо в колонку 21
        river_tiles.append((20, 19, 'n_e'))
        river_tiles.append((21, 19, 'w_s'))
        # r=20..29: колонка 21 (через 3-й мост на (21, 23))
        for r in range(20, self.rows):
            river_tiles.append((21, r, 'straight'))

        for c, r, flow_type in river_tiles:
            if self.is_valid(c, r):
                self.grid[r][c] = TILE_WATER
                self.river_data[(c, r)] = flow_type

    def _carve_road(self) -> None:
        """Прокладывает дорогу шириной в 3 тайла (осевая линия ± 1 тайл) и широкие мосты."""
        bridge_tiles = set()
        for bc, br in self.bridge_coords:
            for dr in (-1, 0, 1):
                if self.is_valid(bc, br + dr):
                    bridge_tiles.add((bc, br + dr))

        def paint_brush(cc: int, rr: int, max_col: int) -> None:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    tc, tr = cc + dc, rr + dr
                    if not self.is_valid(tc, tr) or tc > max_col:
                        continue
                    if (tc, tr) in bridge_tiles or self.grid[tr][tc] == TILE_WATER:
                        self.grid[tr][tc] = TILE_BRIDGE
                    else:
                        self.grid[tr][tc] = TILE_ROAD

        for i in range(len(self.road_nodes) - 1):
            c1, r1 = self.road_nodes[i]
            c2, r2 = self.road_nodes[i + 1]
            # На последнем участке не выходим правее входа в Командный лагерь
            max_col = 37 if i == len(self.road_nodes) - 2 else self.cols - 1

            col_step = 1 if c2 >= c1 else -1
            for c in range(c1, c2 + col_step, col_step):
                paint_brush(c, r1, max_col)

            row_step = 1 if r2 >= r1 else -1
            for r in range(r1, r2 + row_step, row_step):
                paint_brush(c2, r, max_col)

    def _place_build_spots(self) -> None:
        """Размещает 9 ключевых строительных площадок вдоль тропы."""
        for c, r in BUILD_SPOTS_COORDS:
            if self.is_valid(c, r):
                self.grid[r][c] = TILE_BUILD_SPOT

    def _place_fortresses(self) -> None:
        """Размещает 4x4 зону Командного лагеря справа (cols 36..39, rows 13..16)."""
        for r in range(13, 17):
            for c in range(36, 40):
                if self.is_valid(c, r):
                    self.grid[r][c] = TILE_CASTLE

    def _place_forests_and_props(self) -> None:
        """Размещает лесные рощи, валуны, брёвна, кусты и указатели на карте 40x30."""
        # 0 = могучий дуб, 1 = валун, 2 = поваленное бревно, 3 = куст
        obstacle_data = [
            # Верхняя опушка (между элементами HUD на y=0..68)
            (1, 4, 0), (3, 3, 3), (0, 4, 2),
            (10, 1, 0), (12, 0, 3), (27, 1, 0), (29, 1, 3),
            # Северо-восточная дубрава над Командным лагерем
            (30, 4, 0), (33, 3, 1), (35, 5, 0), (38, 4, 3),
            (29, 7, 3), (32, 8, 0), (36, 8, 0), (38, 10, 2),
            (31, 10, 1), (35, 11, 3),
            # Западные луга слева от тракта (свободный проход для A*)
            (0, 11, 3), (1, 14, 0), (5, 13, 1), (7, 14, 2),
            (2, 18, 0), (6, 19, 3), (1, 22, 0), (4, 24, 1),
            (7, 25, 0), (2, 27, 3), (5, 28, 2),
            # Центральные рощи и излучина реки
            (16, 7, 1), (17, 8, 0), (11, 8, 3), (22, 9, 2),
            (28, 7, 0), (28, 10, 3),
            (15, 15, 0), (17, 14, 3), (14, 19, 2), (17, 17, 1),
            (22, 14, 0), (25, 15, 1), (22, 17, 3), (26, 17, 2),
            # Юго-восточная и южная опушки
            (37, 20, 0), (39, 22, 3), (34, 23, 0), (32, 26, 1),
            (36, 25, 0), (38, 27, 2), (31, 28, 3),
            (9, 27, 0), (12, 28, 3), (18, 27, 0), (23, 27, 2),
            (26, 28, 0), (29, 27, 3),
        ]
        for c, r, variant in obstacle_data:
            if self.is_valid(c, r) and self.grid[r][c] == TILE_GRASS:
                self.grid[r][c] = TILE_OBSTACLE
                self.obstacle_variants[(c, r)] = variant

        # Два дорожных указателя вдоль маршрута (снаружи от 3-тайловой дороги)
        self.signposts = [(8, 6), (35, 18)]
        self.signpost_pos = self.signposts[0]

    def is_valid(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def get_tile(self, col: int, row: int) -> int:
        if self.is_valid(col, row):
            return self.grid[row][col]
        return TILE_OBSTACLE

    def is_walkable(self, col: int, row: int) -> bool:
        """Проходимость для героя: обход препятствий, реки, площадок, башен, стен замка и портала."""
        if not self.is_valid(col, row):
            return False
        tile = self.grid[row][col]
        return tile not in (TILE_OBSTACLE, TILE_WATER, TILE_BUILD_SPOT, TILE_TOWER, TILE_CASTLE, TILE_SPAWN)

    def is_buildable(self, col: int, row: int) -> bool:
        """Строительство разрешено ТОЛЬКО на свободных фиксированных площадках."""
        if not self.is_valid(col, row):
            return False
        return self.grid[row][col] == TILE_BUILD_SPOT

    def place_tower(self, col: int, row: int) -> None:
        """Пометить клетку как занятую башней (блокирует A* и повторное строительство)."""
        if self.is_valid(col, row):
            self.grid[row][col] = TILE_TOWER

    def remove_tower(self, col: int, row: int) -> None:
        """Освободить клетку при продаже башни (возвращает статус свободной площадки)."""
        if self.is_valid(col, row) and (col, row) in BUILD_SPOTS_COORDS:
            self.grid[row][col] = TILE_BUILD_SPOT

    def grid_to_pixel(self, col: int, row: int) -> Tuple[int, int]:
        px = self.offset_x + col * self.tile_size
        py = self.offset_y + row * self.tile_size
        return px, py

    def grid_to_center_pixel(self, col: int, row: int) -> Tuple[int, int]:
        px, py = self.grid_to_pixel(col, row)
        return px + self.tile_size // 2, py + self.tile_size // 2

    def pixel_to_grid(self, px: int, py: int) -> Optional[Tuple[int, int]]:
        col = (px - self.offset_x) // self.tile_size
        row = (py - self.offset_y) // self.tile_size
        if self.is_valid(col, row):
            return col, row
        return None

    def is_pixel_in_bounds(self, px: int, py: int) -> bool:
        """Проверяет, попадают ли пиксельные координаты в пределы сетки карты."""
        return self.pixel_to_grid(px, py) is not None

    _INNER_CORNER_MAP = {
        (False, False, False, False): "dirt",
        (True, False, False, False): "in_nw",
        (False, True, False, False): "in_ne",
        (False, False, True, False): "in_sw",
        (False, False, False, True): "in_se",
        (True, True, False, False): "in_nw_ne",
        (True, False, True, False): "in_nw_sw",
        (True, False, False, True): "in_nw_se",
        (False, True, True, False): "in_ne_sw",
        (False, True, False, True): "in_ne_se",
        (False, False, True, True): "in_sw_se",
        (False, True, True, True): "in_ne_sw_se",
        (True, False, True, True): "in_nw_sw_se",
        (True, True, True, False): "in_nw_ne_sw",
        (True, True, False, True): "in_nw_ne_se",
        (True, True, True, True): "in_all",
    }

    def _get_road_autotile_key(self, col: int, row: int) -> Tuple[str, int]:
        """Возвращает ключ автотайла и индекс вариации для 8-направленной дороги."""
        def is_path(c: int, r: int) -> bool:
            # Левый край карты (дорога уходит за пределы экрана на rows 6..8)
            if c < 0 and 6 <= r <= 8:
                return True
            if not self.is_valid(c, r):
                return False
            t = self.grid[r][c]
            return t in (TILE_ROAD, TILE_BRIDGE, TILE_SPAWN, TILE_CASTLE)

        n = is_path(col, row - 1)
        s = is_path(col, row + 1)
        w = is_path(col - 1, row)
        e = is_path(col + 1, row)
        variant = _pseudo_hash(col, row, 19.7)

        # 1. Все 4 кардинальных соседа — дорога: проверяем диагонали (центр и внутренние углы)
        if n and s and w and e:
            nw = is_path(col - 1, row - 1)
            ne = is_path(col + 1, row - 1)
            sw = is_path(col - 1, row + 1)
            se = is_path(col + 1, row + 1)
            key = self._INNER_CORNER_MAP[(not nw, not ne, not sw, not se)]
            return key, variant

        # 2. Прямые края с травой (ровно 1 кардинальный сосед — не дорога)
        if not n and s and w and e:
            return "edge_n", variant
        if not s and n and w and e:
            return "edge_s", variant
        if not w and n and s and e:
            return "edge_w", variant
        if not e and n and s and w:
            return "edge_e", variant

        # 3. Внешние выпуклые углы (трава с 2 смежных сторон)
        if s and e and not n and not w:
            return "c_se", variant
        if s and w and not n and not e:
            return "c_sw", variant
        if n and e and not s and not w:
            return "c_ne", variant
        if n and w and not s and not e:
            return "c_nw", variant

        # 4. Узкие каналы и тупики (fallback)
        if w and e and not n and not s:
            return "h", variant
        if n and s and not w and not e:
            return "v", variant
        if e and not n and not s and not w:
            return "cap_w", variant
        if w and not n and not s and not e:
            return "cap_e", variant
        if s and not n and not w and not e:
            return "cap_n", variant
        if n and not s and not w and not e:
            return "cap_s", variant
        return "iso", variant

    def _get_road_style(self, col: int, row: int) -> str:
        """Совместимость: возвращает базовый стиль сегмента дороги."""
        return self._get_road_autotile_key(col, row)[0]

    def draw(self, surface: pygame.Surface, anim_time: Optional[float] = None) -> None:
        """Отрисовывает диораму 960x720 (сетка 40x30 тайлов, без чёрных полос)."""
        # 1. Заполняем верхние/нижние поля, только если виртуальное поле ниже карты
        if self.offset_y > 0:
            top_y = self.offset_y - self.tile_size
            bot_y = self.offset_y + self.rows * self.tile_size
            for c in range(self.cols):
                px = self.offset_x + c * self.tile_size
                surface.blit(get_grass_tile(0), (px, top_y))
                surface.blit(get_grass_tile(0), (px, bot_y))
            surface.blit(get_river_tile('straight', 0), (self.offset_x + 20 * self.tile_size, top_y))
            surface.blit(get_river_tile('straight', 1), (self.offset_x + 21 * self.tile_size, bot_y))

        # Боковые лесные отступы (если offset_x > 0)
        if self.offset_x > 0:
            forest_strip = get_forest_border()
            surface.blit(forest_strip, (0, self.offset_y))
            surface.blit(forest_strip, (self.offset_x + self.cols * self.tile_size, self.offset_y))

        # 2. Базовый травяной покров (FieldsTile_38.png + цветы/трава)
        for r in range(self.rows):
            for c in range(self.cols):
                px, py = self.grid_to_pixel(c, r)
                v = self.grass_variants.get((c, r), 0)
                surface.blit(get_grass_tile(v), (px, py))

        # 3. Мощёная широкая дорога из тайлсета 1 Tiles/ (8-направленный автотайлинг)
        for r in range(self.rows):
            for c in range(self.cols):
                t = self.grid[r][c]
                if t in (TILE_ROAD, TILE_SPAWN, TILE_CASTLE):
                    px, py = self.grid_to_pixel(c, r)
                    key, variant = self._get_road_autotile_key(c, r)
                    surface.blit(get_road_autotile(key, variant), (px, py))

        # Деревянные пограничные столбики у левого въезда (rows 6..8)
        _, entry_r6_py = self.grid_to_pixel(0, 6)
        _, entry_r8_py = self.grid_to_pixel(0, 8)
        border_post = get_signpost_tile()
        if border_post:
            sc_post = pygame.transform.scale(border_post, (14, 18))
            surface.blit(sc_post, (2, entry_r6_py - 16))
            surface.blit(sc_post, (2, entry_r8_py + 21))

        # 4. Изгибы реки с водными бликами (включая воду под мостами)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] in (TILE_WATER, TILE_BRIDGE):
                    flow = self.river_data.get((c, r), 'straight')
                    px, py = self.grid_to_pixel(c, r)
                    surface.blit(get_river_tile(flow, r % 2), (px, py))

        # 5. Три широких деревянных моста (высотой 3 тайла) через реку
        wide_bridge = get_wide_bridge_tile()
        for bc, br in self.bridge_coords:
            b_px, b_py = self.grid_to_pixel(bc, br - 1)
            surface.blit(wide_bridge, (b_px, b_py))

        # 6. Строительные площадки (PlaceForTower1, 38x30)
        spot_tile = get_build_spot_tile()
        for c, r in BUILD_SPOTS_COORDS:
            if self.is_valid(c, r):
                bpx, bpy = self.grid_to_pixel(c, r)
                surface.blit(spot_tile, (bpx - 7, bpy - 3))

        # 7. Препятствия (крупные деревья 38x48, валуны, брёвна, кусты)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == TILE_OBSTACLE:
                    px, py = self.grid_to_pixel(c, r)
                    v = self.obstacle_variants.get((c, r), 0)
                    obs_tile = get_obstacle_tile(v)
                    if v == 0:
                        surface.blit(obs_tile, (px - 7, py - 24))
                    elif v == 3:
                        surface.blit(obs_tile, (px - 4, py - 2))
                    else:
                        surface.blit(obs_tile, (px - 3, py - 3))

        # 8. Дорожные указатели
        for sc, sr in getattr(self, 'signposts', [self.signpost_pos]):
            spx, spy = self.grid_to_pixel(sc, sr)
            surface.blit(get_signpost_tile(), (spx - 1, spy - 4))

        # 9. Командный Лагерь 4x4 (96x96 px) справа с анимированным костром и флагом
        castle_px, castle_py = self.grid_to_pixel(36, 13)
        t = anim_time if anim_time is not None else getattr(self, 'anim_time', pygame.time.get_ticks() / 1000.0)
        surface.blit(get_castle_3x3(t), (castle_px, castle_py))

        # 10. Внешняя рамка карты
        map_rect = pygame.Rect(0, 0, surface.get_width(), surface.get_height())
        pygame.draw.rect(surface, (135, 145, 60), map_rect, 1)
