"""
Автоматические тесты для Этапа 7 (Рыцарь-командир без старых навыков + Главное меню + HUD + EndScreen):
- Проверка инициализации Рыцаря-командира с PNG-спрайтами (idle/walk/attack) и перемещения по ПКМ (A*)
- Проверка отсутствия старых навыков Q/W/пассивки в settings и Hero
- Проверка Главного меню: MAIN, HERO_SELECT, RECORDS, CONTROLS и запуск игры
- Проверка HUD (только медальон [C]) и кнопок «В главное меню» на экранах Паузы и Победы/Поражения
"""

import os
import sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from settings import (
    HEROES,
    DEFAULT_HERO_ID,
    GRID_COLS,
    GRID_ROWS,
    BUILD_SPOTS_COORDS,
    TOWERS,
    ENEMIES,
    WAVES_CONFIG,
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
)
from core.assets import (
    init_assets,
    get_tower_idle_frames,
    get_tower_upgrade_frames,
    get_tower_unit_frames,
    get_enemy_animations,
    get_arrow_sprite,
    get_mage_projectile_sprite,
)
from core.map import GameMap
from core.wave_manager import WaveManager
from entities.hero import Hero
from entities.enemy import Enemy
from entities.tower import Tower, TowerMenu
from entities.projectile import Projectile
from ui.menu import MainMenu
from ui.hud import HUD
from ui.end_screen import EndScreen
from vfx.particles import ParticleSystem
from vfx.floating_text import FloatingTextManager


def test_stage7():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    init_assets()

    particle_sys = ParticleSystem()
    floating_texts = FloatingTextManager()

    # 1. Проверка Рыцаря-командира
    assert DEFAULT_HERO_ID == "knight"
    assert "knight" in HEROES
    assert "skill_q" not in HEROES["knight"]
    assert "skill_w" not in HEROES["knight"]
    assert "passive" not in HEROES["knight"]

    knight = Hero(start_grid_pos=(35, 16), hero_id="knight")
    assert knight.hero_id == "knight"
    assert knight.hp == HEROES["knight"]["hp"]
    assert knight.name == HEROES["knight"]["name"]
    assert len(knight.idle_frames) == 8
    assert len(knight.walk_frames) == 6
    assert len(knight.attack1_frames) == 4
    assert len(knight.attack2_frames) == 4
    assert len(knight.attack_frames) == 4
    knight_fig_h = knight.idle_frames[0].get_bounding_rect(min_alpha=10).h
    assert 34 <= knight_fig_h <= 42, f"Рост рыцаря должен быть 34..42 px, получено {knight_fig_h}"
    from core.assets import get_hero_portrait
    assert get_hero_portrait("knight").get_width() >= 48

    enemy_k = Enemy("goblin", [(knight.x + 15, knight.y)])
    knight.attack_enemy(enemy_k, particle_sys, floating_texts)
    assert knight.attack_timer > 0.0
    assert knight.attack_combo_index == 1
    first_atk_frames = knight.attack_frames
    knight.attack_enemy(enemy_k, particle_sys, floating_texts)
    assert knight.attack_combo_index == 2
    assert knight.attack_frames is not first_atk_frames or len(knight.attack_variants) == 1

    # Перемещение по ПКМ (A*) через мост и проверка сетки 40x30 (960x720 -> 1440x1080)
    assert WINDOW_WIDTH == 1440 and WINDOW_HEIGHT == 1080
    assert VIRTUAL_WIDTH == 960 and VIRTUAL_HEIGHT == 720
    test_map = GameMap()
    assert test_map.cols == 40 and test_map.rows == 30
    assert len(BUILD_SPOTS_COORDS) == 9
    for sc, sr in BUILD_SPOTS_COORDS:
        assert test_map.is_buildable(sc, sr), f"Площадка ({sc}, {sr}) должна быть доступна для стройки"
    assert test_map.is_pixel_in_bounds(959, 719)
    assert not test_map.is_pixel_in_bounds(-50, -50)

    # Пересчёт координат мыши из физического окна 1440x1080 в 960x720 (масштаб x1.5)
    target_px = test_map.grid_to_center_pixel(10, 11)  # путь A* через центральный мост (19, 11)
    win_mx = round(target_px[0] * WINDOW_WIDTH / VIRTUAL_WIDTH)
    win_my = round(target_px[1] * WINDOW_HEIGHT / VIRTUAL_HEIGHT)
    vx = win_mx * VIRTUAL_WIDTH // WINDOW_WIDTH
    vy = win_my * VIRTUAL_HEIGHT // WINDOW_HEIGHT
    assert abs(vx - target_px[0]) <= 1 and abs(vy - target_px[1]) <= 1
    assert knight.set_destination((vx, vy), test_map)
    assert len(knight.waypoints) >= 2
    assert knight.move_to_pixel(target_px[0] + 4, target_px[1] + 4, test_map)
    assert knight.target_marker is not None

    # 2. Проверка Главного меню
    menu = MainMenu()
    assert menu.state == MainMenu.STATE_MAIN

    click_play = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1})
    res = menu.handle_event(click_play, (menu.btn_play.centerx, menu.btn_play.centery))
    assert res is None
    assert menu.state == MainMenu.STATE_HERO_SELECT
    menu.draw(screen)

    knight_card_rect = menu.hero_cards["knight"]
    menu.handle_event(click_play, (knight_card_rect.centerx, knight_card_rect.centery))
    assert menu.selected_hero_id == "knight"

    start_res = menu.handle_event(click_play, (menu.btn_start_game.centerx, menu.btn_start_game.centery))
    assert start_res is not None
    assert start_res["action"] == "start_game"
    assert start_res["hero_id"] == "knight"

    menu.state = MainMenu.STATE_MAIN
    menu.handle_event(click_play, (menu.btn_records.centerx, menu.btn_records.centery))
    assert menu.state == MainMenu.STATE_RECORDS
    menu.draw(screen)

    menu.handle_event(click_play, (menu.btn_back_records.centerx, menu.btn_back_records.centery))
    assert menu.state == MainMenu.STATE_MAIN

    menu.handle_event(click_play, (menu.btn_controls.centerx, menu.btn_controls.centery))
    assert menu.state == MainMenu.STATE_CONTROLS
    menu.draw(screen)

    menu.handle_event(click_play, (menu.btn_back_controls.centerx, menu.btn_back_controls.centery))
    assert menu.state == MainMenu.STATE_MAIN

    # 3. Проверка HUD (только [C] без кнопок Q/W) и EndScreen
    hud = HUD()
    assert hasattr(hud, "btn_hero_card_rect")
    assert not hasattr(hud, "btn_skill_q_rect")
    assert not hasattr(hud, "btn_skill_w_rect")
    assert hasattr(hud, "btn_pause_resume_rect")
    assert hasattr(hud, "btn_pause_menu_rect")
    hud.draw(screen, hero=knight)

    from ui.high_scores import RECORDS_FILE
    backup_records = None
    if os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            backup_records = f.read()

    try:
        end_scr = EndScreen()
        end_scr.show("victory", "Рыцарь-командир", 20, 500, 50, 10)
        assert end_scr.is_active
        menu_click_res = end_scr.handle_click(end_scr.btn_menu_rect.centerx, end_scr.btn_menu_rect.centery)
        assert menu_click_res == "menu"
        assert not end_scr.is_active
    finally:
        if backup_records is not None:
            with open(RECORDS_FILE, "w", encoding="utf-8") as f:
                f.write(backup_records)

    # 4. Проверка Башни лучников и Башни магов (PNG-ассеты 1-7, юниты, снаряды, сплеш и TowerMenu)
    assert set(TOWERS.keys()) == {"archer", "mage"}, f"Ожидались archer и mage, найдено: {list(TOWERS.keys())}"
    for t_type in ("archer", "mage"):
        for lvl in range(1, 8):
            assert len(get_tower_idle_frames(t_type, lvl)) >= 1
            assert len(get_tower_upgrade_frames(t_type, lvl)) == 4
        for tier in (1, 2, 3):
            for d_key in ("D", "S", "U"):
                assert len(get_tower_unit_frames(t_type, tier, d_key, "Idle")) == 4
                assert len(get_tower_unit_frames(t_type, tier, d_key, "Attack")) == 6
    assert get_arrow_sprite().get_width() >= 10
    for p_tier in (1, 2, 3):
        assert get_mage_projectile_sprite(p_tier).get_width() >= 5

    spot = BUILD_SPOTS_COORDS[0]
    t_menu = TowerMenu()
    t_menu.open_for_spot(spot)
    btn_types = [b["tower_type"] for b in t_menu.buttons]
    assert btn_types == ["archer", "mage"], f"Кнопки меню постройки: {btn_types}"
    t_menu.draw(screen, 500)

    # Башня лучников: выстрел стрелой и апгрейд до 7 уровня
    archer_t = Tower("archer", spot)
    projectiles = []
    target1 = Enemy("goblin", [(archer_t.x + 40, archer_t.y + 10)])
    archer_t.upgrade_anim_timer = 0.0
    archer_t.update(0.1, [target1], projectiles)
    assert len(projectiles) == 1 and projectiles[0].p_type == "arrow"
    archer_t.draw(screen)
    projectiles[0].draw(screen)

    while archer_t.can_upgrade:
        assert archer_t.upgrade()
    assert archer_t.level == 7

    # Башня магов: выстрел магической сферой со сплешем и замедлением
    mage_spot = BUILD_SPOTS_COORDS[1]
    mage_t = Tower("mage", mage_spot)
    mage_t.upgrade_anim_timer = 0.0
    m_target = Enemy("goblin", [(mage_t.x + 35, mage_t.y + 8)])
    m_splash_ally = Enemy("wolf", [(m_target.x + 15, m_target.y)])
    m_projs = []
    mage_t.update(0.1, [m_target, m_splash_ally], m_projs)
    assert len(m_projs) == 1 and m_projs[0].p_type == "magic_orb"
    assert m_projs[0].splash_radius > 0 and m_projs[0].slow_ratio > 0
    mage_t.draw(screen)
    m_projs[0].draw(screen)
    # Доводим сферу до цели и проверяем сплеш + замедление
    for _ in range(30):
        m_projs[0].update(0.05, [m_target, m_splash_ally], particle_sys, floating_texts)
        if not m_projs[0].is_alive:
            break
    assert not m_projs[0].is_alive
    assert m_splash_ally.slow_timer > 0.0

    while mage_t.can_upgrade:
        assert mage_t.upgrade()
    assert mage_t.level == 7
    t_menu.open_for_tower(mage_t)
    assert len(t_menu.buttons) == 2
    t_menu.draw(screen, 500)

    # 5. Проверка 4 новых PNG-врагов (Слизень, Пчела, Гоблин с дубиной, Волк) и 10 волн
    assert set(ENEMIES.keys()) == {"slime", "bee", "goblin", "wolf"}
    assert len(WAVES_CONFIG) == 10
    for w_cfg in WAVES_CONFIG:
        for etype, _ in w_cfg["enemies"]:
            assert etype in ENEMIES, f"Неизвестный враг в волне: {etype}"

    for etype in ("slime", "bee", "goblin", "wolf"):
        e_anims = get_enemy_animations(etype)
        for a_key in ("walk", "attack", "death"):
            for d_key in ("D", "S", "U"):
                assert len(e_anims[a_key][d_key]) == 6
        e = Enemy(etype, [(100.0, 100.0), (200.0, 100.0), (200.0, 200.0), (100.0, 200.0), (100.0, 100.0)])
        e.update(0.1)
        assert e.dir_key == "S" and not e.facing_left  # вправо
        e.draw(screen)
        e.take_damage(9999, ignore_armor=True)
        assert e.is_dying and not e.is_alive
        e.draw(screen)
        e.update(0.6)
        assert e.death_finished

    wm_test = WaveManager(test_map.road_nodes)
    wm_test.current_wave = 4  # следующая волна 5 — мини-босс Гоблин
    assert wm_test.start_next_wave()
    assert any(et == "goblin" and is_b for et, is_b in wm_test.spawn_queue)
    wm_test.wave_state = "completed"
    wm_test.current_wave = 9  # следующая волна 10 — Король гоблинов
    assert wm_test.start_next_wave()
    assert any(et == "goblin" and is_b for et, is_b in wm_test.spawn_queue)
    boss_goblin = Enemy("goblin", [(100.0, 100.0)], wave_index=9, is_boss=True)
    boss_goblin.draw(screen)

    print("ВСЕ ТЕСТЫ ЭТАПА 7 УСПЕШНО ПРОЙДЕНЫ!")


if __name__ == "__main__":
    test_stage7()
