"""
Конфигурация и константы баланса игры «Королевство в опасности».
"""

# --- Параметры экрана и рендеринга (4:3, масштаб x1.5 в 1440x1080) ---
VIRTUAL_WIDTH = 960
VIRTUAL_HEIGHT = 720
WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 1080
FPS = 60

# --- Сетка карты (40x30 тайлов 24x24 на виртуальном экране 960x720) ---
TILE_SIZE = 24
GRID_COLS = 40
GRID_ROWS = 30
MAP_WIDTH = GRID_COLS * TILE_SIZE    # 960 px
MAP_HEIGHT = GRID_ROWS * TILE_SIZE   # 720 px
MAP_OFFSET_X = (VIRTUAL_WIDTH - MAP_WIDTH) // 2   # 0 px
MAP_OFFSET_Y = (VIRTUAL_HEIGHT - MAP_HEIGHT) // 2 # 0 px (полное заполнение без полос)

# --- Плавающий интерфейс (HUD) ---
HUD_HEIGHT = 0  # Панель теперь плавающая поверх карты без блокировки экрана

# --- Типы тайлов ---
TILE_GRASS = 0     # Трава: проходима героем, доступна для постройки башен
TILE_ROAD = 1      # Дорога: путь наступления врагов, проходима героем, строить нельзя
TILE_OBSTACLE = 2  # Препятствие (скалы/деревья): непроходимо, строить нельзя
TILE_SPAWN = 3     # Точка появления волн (портал/ворота врага)
TILE_CASTLE = 4    # Ворота Замка (цель врагов, точка возрождения героя)
TILE_WATER = 5     # Река / ручей: непроходимо, строить нельзя
TILE_BRIDGE = 6    # Деревянный мост: проходим для героя и врагов, строить нельзя
TILE_BUILD_SPOT = 7  # Фиксированная строительная площадка для башен (стиль Kingdom Rush)
TILE_TOWER = 8       # Построенная оборонительная башня

# --- Координаты 9 ключевых строительных площадок вдоль 3-тайловой дороги (сетка 40x30) ---
BUILD_SPOTS_COORDS = [
    (3, 10),   # Западный карман после входа
    (13, 7),   # Северный фланг перед 1-м мостом
    (22, 7),   # Восточный фланг за 1-м мостом
    (13, 16),  # Центральная развилка между дорогами
    (16, 20),  # Юго-западный поворот перед 3-м мостом
    (24, 19),  # Восточная петля за 3-м мостом
    (27, 13),  # Укрепление на восточном фланге
    (33, 19),  # Южный подход к Командному лагерю
    (14, 26),  # Южный бастион под нижней дорогой
]

# --- Цветовая палитра (пиксель-арт) ---
COLOR_BG = (15, 17, 24)
COLOR_GRID_LINE = (28, 32, 44)
COLOR_GRASS_BASE = (36, 118, 48)
COLOR_GRASS_ACCENT = (48, 142, 62)
COLOR_ROAD_BASE = (175, 136, 92)
COLOR_ROAD_STONE = (145, 108, 70)
COLOR_OBSTACLE = (52, 60, 72)
COLOR_SPAWN = (168, 44, 44)
COLOR_CASTLE = (78, 92, 120)

COLOR_UI_BG = (22, 24, 34)
COLOR_UI_PANEL = (32, 36, 50)
COLOR_UI_BORDER = (90, 75, 52)
COLOR_UI_BORDER_BRIGHT = (180, 145, 75)
COLOR_UI_TEXT = (235, 235, 240)
COLOR_UI_TEXT_MUTED = (140, 145, 165)
COLOR_GOLD = (245, 200, 50)
COLOR_HP = (220, 50, 50)
COLOR_XP = (70, 160, 245)

# --- Экономика и игровой баланс ---
STARTING_GOLD = 350
CASTLE_MAX_HP = 20
HERO_RESPAWN_TIME = 12.0
HERO_RESPAWN_GOLD_PENALTY = 0.30

# --- Спецификация героев-командиров (только базовые статы; система навыков будет добавлена заново) ---
HEROES = {
    "knight": {
        "id": "knight",
        "name": "Рыцарь-командир",
        "title": "Защитник короны",
        "color": (210, 215, 230),
        "hp": 175,
        "speed": 92.0,
        "attack_damage": 14,
        "attack_range": 36.0,
        "attack_cooldown": 0.75,
    },
}

DEFAULT_HERO_ID = "knight"

# --- Бестиарий врагов (PNG-ассеты в assets/enemies/, масштаб 960x720) ---
ENEMIES = {
    "slime": {
        "id": "slime",
        "name": "Слизень",
        "hp": 34,
        "speed": 72.0,
        "reward_gold": 7,
        "reward_xp": 10,
        "castle_damage": 1,
        "attack_damage": 5,
        "size": (26, 26),
        "armor": 0.0,
    },
    "bee": {
        "id": "bee",
        "name": "Гигантская пчела",
        "hp": 42,
        "speed": 116.0,
        "reward_gold": 9,
        "reward_xp": 14,
        "castle_damage": 1,
        "attack_damage": 6,
        "size": (28, 28),
        "armor": 0.0,
    },
    "goblin": {
        "id": "goblin",
        "name": "Гоблин с дубиной",
        "hp": 110,
        "speed": 76.0,
        "reward_gold": 18,
        "reward_xp": 26,
        "castle_damage": 2,
        "attack_damage": 12,
        "size": (32, 34),
        "armor": 0.05,
    },
    "wolf": {
        "id": "wolf",
        "name": "Свирепый волк",
        "hp": 85,
        "speed": 132.0,
        "reward_gold": 15,
        "reward_xp": 22,
        "castle_damage": 1,
        "attack_damage": 11,
        "size": (34, 30),
        "armor": 0.0,
    },
}

# --- Параметры волн ---
TOTAL_WAVES = 10
WAVE_HP_SCALE = 0.12        # +12% HP врагов за каждую следующую волну
WAVE_REWARD_SCALE = 0.05    # +5% золота за каждую следующую волну
WAVE_SPAWN_INTERVAL = 1.2   # Секунды между выходом врагов из портала

# 10 сбалансированных волн на базе 4 типов врагов (Слизень, Пчела, Гоблин, Волк)
WAVES_CONFIG = [
    # Волна 1: Массовый выход слизней
    {"enemies": [("slime", 7)], "desc": "Полчище слизней"},
    # Волна 2: Слизни и быстрые пчёлы
    {"enemies": [("slime", 6), ("bee", 5)], "desc": "Ядовитый рой"},
    # Волна 3: Первые гоблины с дубинами
    {"enemies": [("slime", 8), ("bee", 6), ("goblin", 3)], "desc": "Разведка гоблинов"},
    # Волна 4: Подключение быстрых волков
    {"enemies": [("bee", 8), ("goblin", 6), ("wolf", 3)], "desc": "Волчья стая"},
    # Волна 5: МИНИ-БОСС — Вожак гоблинов с короной
    {"enemies": [("slime", 8), ("wolf", 4), ("goblin", 5)], "boss_wave": True, "boss_type": "goblin", "desc": "Вожак гоблинов"},
    # Волна 6: Ускоренный натиск
    {"enemies": [("bee", 10), ("wolf", 6), ("goblin", 6)], "desc": "Стремительный прорыв"},
    # Волна 7: Плотное наступление лесной орды
    {"enemies": [("slime", 12), ("goblin", 9), ("wolf", 6)], "desc": "Натиск лесной орды"},
    # Волна 8: Охотничьи стаи и рои
    {"enemies": [("bee", 12), ("wolf", 9), ("goblin", 8)], "desc": "Охота клыков и жал"},
    # Волна 9: Массированный штурм всех 4 видов врагов
    {"enemies": [("slime", 14), ("bee", 10), ("wolf", 10), ("goblin", 10)], "desc": "Массированный штурм"},
    # Волна 10: ФИНАЛЬНЫЙ БОСС — Король гоблинов с армией
    {"enemies": [("wolf", 10), ("bee", 10), ("goblin", 10)], "boss_wave": True, "final_boss": True, "boss_type": "goblin", "desc": "Финальная битва: Король гоблинов"},
]

# --- Оборонительные башни (Башня лучников и Башня магов, уровни 1-7 под сетку 40x30) ---
TOWERS = {
    "archer": {
        "id": "archer",
        "name": "Башня лучников",
        "desc": "Скорострельные лучники со стрелами по целям",
        "projectile_type": "arrow",
        "color": (95, 185, 115),
        "levels": {
            1: {"cost": 70,  "range": 130.0, "damage": 14, "cooldown": 0.90, "name": "Дозорный помост L1"},
            2: {"cost": 85,  "range": 142.0, "damage": 20, "cooldown": 0.82, "name": "Деревянная вышка L2"},
            3: {"cost": 105, "range": 154.0, "damage": 28, "cooldown": 0.75, "name": "Башня следопытов L3"},
            4: {"cost": 130, "range": 166.0, "damage": 38, "cooldown": 0.68, "name": "Укреплённый форт L4"},
            5: {"cost": 160, "range": 178.0, "damage": 50, "cooldown": 0.62, "name": "Каменный бастион L5"},
            6: {"cost": 195, "range": 192.0, "damage": 65, "cooldown": 0.55, "name": "Застава стражей L6"},
            7: {"cost": 240, "range": 208.0, "damage": 85, "cooldown": 0.48, "name": "Цитадель снайперов L7"},
        },
    },
    "mage": {
        "id": "mage",
        "name": "Башня магов",
        "desc": "Магические сферы со сплешем, замедлением и пробитием брони",
        "projectile_type": "magic_orb",
        "color": (175, 105, 250),
        "levels": {
            1: {"cost": 100, "range": 118.0, "damage": 16, "cooldown": 1.65, "splash_radius": 42.0, "slow_ratio": 0.20, "slow_duration": 1.4, "ignore_armor": True, "name": "Рунный курган L1"},
            2: {"cost": 115, "range": 128.0, "damage": 23, "cooldown": 1.55, "splash_radius": 48.0, "slow_ratio": 0.25, "slow_duration": 1.6, "ignore_armor": True, "name": "Грот кристаллов L2"},
            3: {"cost": 135, "range": 138.0, "damage": 32, "cooldown": 1.45, "splash_radius": 54.0, "slow_ratio": 0.30, "slow_duration": 1.8, "ignore_armor": True, "name": "Скальный алтарь L3"},
            4: {"cost": 160, "range": 148.0, "damage": 44, "cooldown": 1.35, "splash_radius": 60.0, "slow_ratio": 0.35, "slow_duration": 2.0, "ignore_armor": True, "name": "Обитель адепта L4"},
            5: {"cost": 190, "range": 158.0, "damage": 58, "cooldown": 1.25, "splash_radius": 66.0, "slow_ratio": 0.40, "slow_duration": 2.2, "ignore_armor": True, "name": "Башня чародеев L5"},
            6: {"cost": 225, "range": 170.0, "damage": 75, "cooldown": 1.15, "splash_radius": 72.0, "slow_ratio": 0.45, "slow_duration": 2.5, "ignore_armor": True, "name": "Чертог колдунов L6"},
            7: {"cost": 270, "range": 184.0, "damage": 98, "cooldown": 1.05, "splash_radius": 80.0, "slow_ratio": 0.50, "slow_duration": 2.8, "ignore_armor": True, "name": "Цитадель архимага L7"},
        },
    },
}

TOWER_SELL_RATIO = 0.70  # Возврат 70% потраченного золота при продаже башни
