"""
Главная точка входа игры «Королевство в опасности».
Режим обороны башнями (система командиров временно отключена для переработки с нуля).
"""

import math
import sys
from typing import Dict, List, Optional, Tuple
import pygame
from settings import (
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    COLOR_BG,
    BUILD_SPOTS_COORDS,
    DEFAULT_HERO_ID,
)
from core.assets import init_assets
from core.map import GameMap
from core.wave_manager import WaveManager
from core.sound import get_sound_manager, play_sound
from entities.hero import Hero
from entities.tower import Tower, TowerMenu
from entities.projectile import Projectile
from ui.hud import HUD
from ui.character_card import CharacterCard
from ui.end_screen import EndScreen
from ui.menu import MainMenu
from vfx.particles import ParticleSystem
from vfx.floating_text import FloatingTextManager
from vfx.camera import CameraShake


def run_game(max_frames: int = 0) -> None:
    """
    Запускает главный игровой цикл.
    Если max_frames > 0, цикл завершается после указанного количества кадров (для автотестов).
    """
    pygame.init()
    pygame.font.init()

    # Физическое окно игры (1280x720)
    window_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Королевство в опасности")

    # Внутренний виртуальный Surface (640x360) и поверхность игрового мира (для сотрясения камеры)
    virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    world_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

    # Инициализация кэша процедурных ассетов и звуковой системы
    init_assets()
    sound_mgr = get_sound_manager()

    # Состояние игры ("MENU" или "GAME")
    # В тестовом режиме сразу стартуем в игре
    game_state = "GAME" if max_frames > 0 else "MENU"
    current_hero_id = DEFAULT_HERO_ID

    # Меню игры
    main_menu = MainMenu()

    # Инициализация систем мира, командира, менеджера волн, HUD, карточки героя и экрана завершения
    game_map = GameMap()
    hero: Optional[Hero] = Hero(start_grid_pos=(35, 16), hero_id=current_hero_id)
    wave_manager = WaveManager(game_map.road_nodes)
    hud = HUD()
    char_card = CharacterCard()
    end_screen = EndScreen()

    # Системы визуальных эффектов (VFX)
    particle_sys = ParticleSystem()
    floating_texts = FloatingTextManager()
    cam_shake = CameraShake()

    # Хранилище построенных башен, снарядов и контекстного меню
    towers: Dict[Tuple[int, int], Tower] = {}
    projectiles: List[Projectile] = []
    tower_menu = TowerMenu()

    def reset_game(hero_id: str = DEFAULT_HERO_ID) -> None:
        """Перезапускает игру с выбранным командиром."""
        nonlocal game_map, hero, wave_manager, current_hero_id
        current_hero_id = hero_id or DEFAULT_HERO_ID
        game_map = GameMap()
        hero = Hero(start_grid_pos=(35, 16), hero_id=current_hero_id)
        wave_manager = WaveManager(game_map.road_nodes)
        towers.clear()
        projectiles.clear()
        tower_menu.close()
        char_card.close()
        end_screen.hide()
        particle_sys.clear()
        floating_texts.clear()
        cam_shake.trauma = 0.0

    # В тестовом режиме стартуем волну и ставим тестовую башню
    if max_frames > 0:
        wave_manager.start_next_wave()
        test_spot = BUILD_SPOTS_COORDS[0]
        towers[test_spot] = Tower("archer", test_spot)
        game_map.place_tower(test_spot[0], test_spot[1])

    clock = pygame.time.Clock()
    running = True
    frame_count = 0
    fps_timer = 0.0

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        fps_timer += dt

        # Координаты мыши в виртуальном пространстве 640x360
        mx, my = pygame.mouse.get_pos()
        vx = mx * VIRTUAL_WIDTH // WINDOW_WIDTH
        vy = my * VIRTUAL_HEIGHT // WINDOW_HEIGHT

        # ==============================================================
        # 1. СОСТОЯНИЕ ГЛАВНОГО МЕНЮ
        # ==============================================================
        if game_state == "MENU":
            main_menu.update(dt)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    action = main_menu.handle_event(event, (vx, vy))
                    if action:
                        act = action.get("action")
                        if act == "quit":
                            running = False
                        elif act == "toggle_sound":
                            sound_mgr.toggle_mute()
                        elif act == "start_game":
                            reset_game(action.get("hero_id", DEFAULT_HERO_ID))
                            game_state = "GAME"

            # Отрисовка меню
            main_menu.draw(virtual_screen, sound_muted=sound_mgr.is_muted)
            pygame.transform.scale(virtual_screen, (WINDOW_WIDTH, WINDOW_HEIGHT), window_surface)
            pygame.display.flip()

            frame_count += 1
            if 0 < max_frames <= frame_count:
                running = False
            continue

        # ==============================================================
        # 2. СОСТОЯНИЕ ИГРОВОГО ПРОЦЕССА (GAMEPLAY)
        # ==============================================================
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if end_screen.is_active:
                        pass
                    elif char_card.is_open:
                        char_card.close()
                    elif tower_menu.is_open:
                        tower_menu.close()
                        for t in towers.values():
                            t.is_selected = False
                    elif wave_manager.is_paused:
                        wave_manager.is_paused = False
                    else:
                        wave_manager.toggle_pause()
                        play_sound("click", 0.7)
                elif event.key == pygame.K_c:
                    if hero is not None and not end_screen.is_active:
                        char_card.toggle()
                        play_sound("click", 0.7)
                elif event.key == pygame.K_p:
                    if not end_screen.is_active:
                        wave_manager.toggle_pause()
                        play_sound("click", 0.7)
                elif event.key == pygame.K_SPACE:
                    if not end_screen.is_active:
                        if wave_manager.can_start_next_wave:
                            wave_manager.start_next_wave()
                            play_sound("click", 0.8)
                        elif wave_manager.is_wave_active:
                            wave_manager.toggle_speed()
                            play_sound("click", 0.7)

            elif event.type == pygame.MOUSEMOTION:
                if end_screen.is_active:
                    end_screen.update_hover(vx, vy)
                elif not char_card.is_open:
                    tower_menu.update_hover(vx, vy)
                    for (tc, tr), tower in towers.items():
                        t_px, t_py = game_map.grid_to_center_pixel(tc, tr)
                        tower.is_hovered = (math.hypot(vx - t_px, vy - (t_py - 8)) <= 24)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # 1. Финальный экран Победы / Поражения
                    if end_screen.is_active:
                        click_res = end_screen.handle_click(vx, vy)
                        if click_res == "restart":
                            reset_game(current_hero_id)
                            continue
                        elif click_res == "menu":
                            game_state = "MENU"
                            main_menu.state = MainMenu.STATE_MAIN
                            continue
                        continue

                    # 2. Если игра на паузе — клики по кнопкам паузы
                    if wave_manager.is_paused:
                        if hud.btn_pause_resume_rect.collidepoint(vx, vy):
                            wave_manager.toggle_pause()
                            play_sound("click", 0.7)
                            continue
                        elif hud.btn_pause_menu_rect.collidepoint(vx, vy):
                            wave_manager.is_paused = False
                            game_state = "MENU"
                            main_menu.state = MainMenu.STATE_MAIN
                            play_sound("click", 0.7)
                            continue

                    # 3. Карточка персонажа
                    if char_card.is_open:
                        if hero is not None and char_card.handle_click(vx, vy, hero, particle_sys, floating_texts):
                            continue
                        char_card.close()

                    # 4. Кнопка звука (Вкл / Выкл) в правом верхнем углу
                    if hud.btn_sound_rect.collidepoint(vx, vy):
                        sound_mgr.toggle_mute()
                        continue

                    # 5. Контекстное всплывающее меню постройки/улучшения/продажи башен
                    if tower_menu.is_open:
                        menu_res = tower_menu.handle_click(vx, vy, wave_manager.gold)
                        act = menu_res.get("action")
                        if act == "build":
                            spot = menu_res["spot"]
                            cost = menu_res["cost"]
                            t_type = menu_res["tower_type"]
                            wave_manager.gold -= cost
                            towers[spot] = Tower(t_type, spot)
                            game_map.place_tower(spot[0], spot[1])
                            play_sound("build", 0.8)
                            particle_sys.add_level_up_sparks(
                                game_map.grid_to_center_pixel(spot[0], spot[1])[0],
                                game_map.grid_to_center_pixel(spot[0], spot[1])[1],
                            )
                            floating_texts.add_status(
                                game_map.grid_to_center_pixel(spot[0], spot[1])[0],
                                game_map.grid_to_center_pixel(spot[0], spot[1])[1] - 14,
                                f"-{cost}g",
                                (255, 140, 100),
                            )
                            continue
                        elif act == "upgrade":
                            u_tower = menu_res["tower"]
                            cost = menu_res["cost"]
                            wave_manager.gold -= cost
                            u_tower.upgrade()
                            play_sound("build", 0.8)
                            particle_sys.add_level_up_sparks(u_tower.x, u_tower.y)
                            floating_texts.add_status(u_tower.x, u_tower.y - 14, f"-{cost}g", (255, 140, 100))
                            continue
                        elif act == "sell":
                            s_tower = menu_res["tower"]
                            spot = menu_res["spot"]
                            refund = menu_res["refund"]
                            wave_manager.gold += refund
                            if spot in towers:
                                del towers[spot]
                            game_map.remove_tower(spot[0], spot[1])
                            play_sound("coin", 0.8)
                            floating_texts.add_gold(s_tower.x, s_tower.y - 14, refund)
                            continue
                        elif act in ("close", "cant_afford"):
                            play_sound("click", 0.6)
                            for t in towers.values():
                                t.is_selected = False
                            continue

                    # 6. Кнопки плавающего HUD (Пауза, Волна, Медальон [C])
                    if hud.btn_pause_rect.collidepoint(vx, vy):
                        wave_manager.toggle_pause()
                        play_sound("click", 0.7)
                        continue
                    elif hud.btn_wave_rect.collidepoint(vx, vy):
                        if wave_manager.can_start_next_wave:
                            wave_manager.start_next_wave()
                            play_sound("click", 0.8)
                        elif wave_manager.is_wave_active:
                            wave_manager.toggle_speed()
                            play_sound("click", 0.7)
                        continue
                    elif hero is not None and hud.btn_hero_card_rect.collidepoint(vx, vy):
                        char_card.toggle()
                        play_sound("click", 0.7)
                        continue

                    # 7. Проверка клика по башням или площадкам под башни
                    clicked_spot = None
                    for spot in BUILD_SPOTS_COORDS:
                        b_px, b_py = game_map.grid_to_center_pixel(spot[0], spot[1])
                        if math.hypot(vx - b_px, vy - b_py) <= 24:
                            clicked_spot = spot
                            break

                    if clicked_spot:
                        play_sound("click", 0.7)
                        for t in towers.values():
                            t.is_selected = False
                        if clicked_spot in towers:
                            existing_tower = towers[clicked_spot]
                            existing_tower.is_selected = True
                            b_px, b_py = game_map.grid_to_center_pixel(clicked_spot[0], clicked_spot[1])
                            tower_menu.open_for_tower(existing_tower, clicked_spot, b_px, b_py - 20)
                        else:
                            b_px, b_py = game_map.grid_to_center_pixel(clicked_spot[0], clicked_spot[1])
                            tower_menu.open_for_spot(clicked_spot, b_px, b_py - 10)
                        continue
                    else:
                        if tower_menu.is_open:
                            tower_menu.close()
                            for t in towers.values():
                                t.is_selected = False

                elif event.button == 3:
                    # Клик ПКМ: Перемещение командира по сетке (A*)
                    if hero is not None and not char_card.is_open and not end_screen.is_active:
                        if game_map.is_pixel_in_bounds(vx, vy):
                            hero.set_destination((vx, vy), game_map)

        # -------------------------------------------------------------
        # Обновление игровой логики
        # -------------------------------------------------------------
        eff_dt = dt * (0.0 if wave_manager.is_paused else wave_manager.game_speed)
        game_map.update(dt)

        if not wave_manager.is_paused and not end_screen.is_active:
            # Обновление волн врагов
            wave_status = wave_manager.update(
                dt=dt,
                hero=hero,
                particle_sys=particle_sys,
                floating_texts=floating_texts,
                cam_shake=cam_shake,
            )

            # Проверка условий победы или поражения
            hero_display_name = hero.name if hero is not None else None
            if wave_status == "defeat" or wave_manager.castle_hp <= 0:
                end_screen.show(
                    outcome="defeat",
                    hero_name=hero_display_name,
                    castle_hp=0,
                    gold=wave_manager.gold,
                    kills=wave_manager.total_enemies_killed,
                    waves_cleared=max(0, wave_manager.current_wave - 1),
                )
            elif wave_status == "victory":
                end_screen.show(
                    outcome="victory",
                    hero_name=hero_display_name,
                    castle_hp=wave_manager.castle_hp,
                    gold=wave_manager.gold,
                    kills=wave_manager.total_enemies_killed,
                    waves_cleared=wave_manager.total_waves,
                )

            # Обновление командира (если активен)
            if hero is not None:
                hero.update(
                    eff_dt,
                    enemies=wave_manager.enemies,
                    particle_sys=particle_sys,
                    floating_texts=floating_texts,
                    cam_shake=cam_shake,
                    wave_manager=wave_manager,
                )

            # Колбэк убийства врага башней
            def on_tower_kill(gold_reward: int, xp_reward: int, ex: float = 0.0, ey: float = 0.0):
                wave_manager.gold += gold_reward
                wave_manager.total_enemies_killed += 1
                if hero is not None:
                    hero.add_xp(xp_reward, particle_sys, floating_texts)

            # Обновление башен
            for tower in list(towers.values()):
                tower.update(eff_dt, wave_manager.enemies, projectiles, on_tower_kill)

            # Обновление снарядов в полёте
            for proj in projectiles:
                proj.update(
                    eff_dt,
                    wave_manager.enemies,
                    particle_sys=particle_sys,
                    floating_texts=floating_texts,
                    cam_shake=cam_shake,
                )
            projectiles = [p for p in projectiles if p.is_alive]

            # Обновление частиц и всплывающих надписей
            particle_sys.update(eff_dt)
            floating_texts.update(eff_dt)

        # Обновление травмы тряски камеры
        cam_shake.update(dt)

        # Обновление FPS в заголовке окна
        if fps_timer >= 0.25:
            fps_timer = 0.0
            actual_fps = int(clock.get_fps())
            speed_label = " | 2x" if wave_manager.game_speed > 1.0 else ""
            pause_label = " | [ПАУЗА]" if wave_manager.is_paused else ""
            hero_status = (
                f" | {hero.name}: Ур.{hero.level} ({int(hero.hp)}/{hero.max_hp}HP)"
                if hero is not None
                else ""
            )
            sound_status = " | [Звук: ВЫКЛ]" if sound_mgr.is_muted else ""
            pygame.display.set_caption(f"Королевство в опасности | FPS: {actual_fps}{speed_label}{pause_label}{hero_status}{sound_status}")

        # --- Отрисовка игрового мира на world_surface ---
        world_surface.fill(COLOR_BG)
        game_map.draw(world_surface)

        # 1. Радиусы атак башен
        for tower in towers.values():
            tower.draw_range(world_surface)

        # 2. 2.5D Y-сортировка всех сущностей (башни, враги, герой если есть)
        all_entities = list(towers.values()) + list(wave_manager.enemies)
        if hero is not None:
            all_entities.append(hero)
        for entity in sorted(all_entities, key=lambda ent: ent.y):
            entity.draw(world_surface)

        # 3. Снаряды
        for proj in projectiles:
            proj.draw(world_surface)

        # 4. Визуальные эффекты (частицы, вихри, волны)
        particle_sys.draw(world_surface)

        # 5. Всплывающий текст (цифры урона, золота, опыта)
        floating_texts.draw(world_surface)

        # --- Перенос мира на виртуальный экран с учётом смещения тряски камеры ---
        cam_dx, cam_dy = cam_shake.get_offset()
        virtual_screen.fill(COLOR_BG)
        virtual_screen.blit(world_surface, (cam_dx, cam_dy))

        # --- Статичные элементы UI поверх экрана (не подвержены тряске) ---
        # 1. Всплывающее меню башен
        tower_menu.draw(virtual_screen, wave_manager.gold)

        # 2. Оповещения волн
        wave_manager.draw_overlays(virtual_screen)

        # 3. Минималистичный плавающий HUD
        hud.draw(
            virtual_screen,
            castle_hp=wave_manager.castle_hp,
            gold=wave_manager.gold,
            wave_num=wave_manager.current_wave,
            total_waves=wave_manager.total_waves,
            is_paused=wave_manager.is_paused,
            is_fast=(wave_manager.game_speed > 1.0),
            can_start_wave=wave_manager.can_start_next_wave,
            hero=hero,
            sound_muted=sound_mgr.is_muted,
        )

        # 4. Карточка персонажа [C] (если герой активен)
        if hero is not None:
            char_card.draw(virtual_screen, hero)

        # 5. Экран Победы / Поражения (поверх всех остальных окон)
        end_screen.draw(virtual_screen)

        # --- Масштабирование виртуального экрана 640x360 в физическое окно 1280x720 ---
        pygame.transform.scale(virtual_screen, (WINDOW_WIDTH, WINDOW_HEIGHT), window_surface)
        pygame.display.flip()

        frame_count += 1
        if 0 < max_frames <= frame_count:
            running = False

    pygame.quit()


if __name__ == "__main__":
    frames = 0
    if len(sys.argv) > 1 and sys.argv[1] == "--test-run":
        frames = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    run_game(max_frames=frames)
