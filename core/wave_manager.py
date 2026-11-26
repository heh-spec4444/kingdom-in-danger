"""
Модуль управления волнами врагов (Этап 3): спавн 10 волн, масштабирование сложности,
урон замку, контроль паузы и ускорения (1x/2x).
"""

import math
import random
from typing import List, Tuple, Dict, Optional
import pygame
from settings import (
    TOTAL_WAVES,
    WAVES_CONFIG,
    WAVE_SPAWN_INTERVAL,
    STARTING_GOLD,
    CASTLE_MAX_HP,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    TILE_SIZE,
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
)
from entities.enemy import Enemy
from core.assets import get_font


class WaveManager:
    """Управляет жизненным циклом 10 волн, спавном врагов и здоровьем Цитадели Замка."""

    def __init__(self, road_nodes: List[Tuple[int, int]]):
        # Преобразование координат сетки тайлов в центральные пиксели для вейпоинтов
        self.waypoints: List[Tuple[float, float]] = [
            (
                float(MAP_OFFSET_X + c * TILE_SIZE + TILE_SIZE // 2),
                float(MAP_OFFSET_Y + r * TILE_SIZE + TILE_SIZE // 2),
            )
            for c, r in road_nodes
        ]

        # Ресурсы и состояние Цитадели
        self.castle_hp = CASTLE_MAX_HP
        self.castle_max_hp = CASTLE_MAX_HP
        self.gold = STARTING_GOLD
        self.total_enemies_killed = 0

        # Управление ходом времени
        self.is_paused = False
        self.game_speed = 1.0  # 1.0x или 2.0x

        # Состояние волн
        self.current_wave = 0
        self.total_waves = TOTAL_WAVES
        # "idle", "spawning", "in_progress", "completed", "victory", "defeat"
        self.wave_state = "idle"

        # Очередь спавна текущей волны
        self.enemies: List[Enemy] = []
        self.spawn_queue: List[Tuple[str, bool]] = []  # [(enemy_type, is_boss), ...]
        self.spawn_timer = 0.0
        self.spawn_interval = WAVE_SPAWN_INTERVAL

        # Визуальные эффекты баннеров волны и урона замку
        self.banner_timer = 0.0
        self.banner_title = ""
        self.banner_subtitle = ""
        self.castle_flash_timer = 0.0

        # Шрифты для оповещений
        self.font_title = get_font(22)
        self.font_sub = get_font(15)

    @property
    def can_start_next_wave(self) -> bool:
        """Можно ли запустить следующую волну."""
        return self.wave_state in ("idle", "completed") and self.current_wave < self.total_waves and self.castle_hp > 0

    @property
    def is_wave_active(self) -> bool:
        """Идёт ли сейчас активная волна (спавн или бой)."""
        return self.wave_state in ("spawning", "in_progress")

    def start_next_wave(self) -> bool:
        """Запускает следующую волну из 10 доступных."""
        if not self.can_start_next_wave:
            return False

        self.current_wave += 1
        cfg = WAVES_CONFIG[self.current_wave - 1]

        # Формируем плоскую очередь монстров
        self.spawn_queue = []
        is_boss_wave = cfg.get("boss_wave", False)
        boss_type = cfg.get("boss_type", "goblin")

        for enemy_type, count in cfg["enemies"]:
            for i in range(count):
                is_boss = False
                if is_boss_wave and enemy_type == boss_type and i == count - 1:
                    is_boss = True
                self.spawn_queue.append((enemy_type, is_boss))

        self.wave_state = "spawning"
        self.spawn_timer = self.spawn_interval  # Чтобы первый монстр появился сразу

        # Баннер оповещения
        self.banner_title = f"ВОЛНА {self.current_wave} ИЗ {self.total_waves}"
        self.banner_subtitle = cfg.get("desc", "Враги наступают!")
        self.banner_timer = 2.4

        return True

    def toggle_pause(self) -> bool:
        """Переключает паузу (клавиша P / ESC / кнопка ||)."""
        self.is_paused = not self.is_paused
        return self.is_paused

    def toggle_speed(self) -> float:
        """Переключает ускорение 1x / 2x (клавиша Space / кнопка >>)."""
        self.game_speed = 2.0 if self.game_speed == 1.0 else 1.0
        return self.game_speed

    def update(
        self,
        dt: float,
        hero=None,
        particle_sys=None,
        floating_texts=None,
        cam_shake=None,
    ) -> None:
        """Обновляет таймеры волн, спавн врагов, движение, бой с героем и урон замку."""
        if self.is_paused:
            return

        eff_dt = dt * self.game_speed

        # Вспышка урона замку
        if self.castle_flash_timer > 0:
            self.castle_flash_timer = max(0.0, self.castle_flash_timer - eff_dt)

        # Таймер центрального баннера
        if self.banner_timer > 0:
            self.banner_timer = max(0.0, self.banner_timer - eff_dt)

        # 1. Спавн врагов из-за левого края карты
        if self.wave_state == "spawning":
            self.spawn_timer += eff_dt
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer = 0.0
                if self.spawn_queue:
                    e_type, is_boss = self.spawn_queue.pop(0)
                    # Небольшой случайный разброс по ширине 3-тайловой дороги (±9 px)
                    enemy_waypoints: List[Tuple[float, float]] = []
                    total_wp = len(self.waypoints)
                    for idx, (wx, wy) in enumerate(self.waypoints):
                        jitter = 4.0 if idx == total_wp - 1 else 9.0
                        enemy_waypoints.append((
                            wx + random.uniform(-jitter, jitter),
                            wy + random.uniform(-jitter, jitter),
                        ))
                    spawn_y = enemy_waypoints[0][1] if enemy_waypoints else 180.0
                    enemy = Enemy(
                        enemy_type=e_type,
                        waypoints=enemy_waypoints,
                        wave_index=self.current_wave - 1,
                        is_boss=is_boss,
                        spawn_x=-16.0,
                        spawn_y=spawn_y,
                    )
                    self.enemies.append(enemy)

                if not self.spawn_queue:
                    self.wave_state = "in_progress"

        # 2. Управление агром врагов на командира (блокировка на линии, максимум 2 врага)
        max_engaged = 2
        if hero is not None and hero.is_alive:
            already_engaged = []
            free_candidates = []
            for enemy in self.enemies:
                if not enemy.is_alive or enemy.reached_castle:
                    continue
                d = math.hypot(enemy.x - hero.x, enemy.y - hero.y)
                # Если уже заагрен — держит агр до 105px
                if enemy.is_engaged:
                    if d <= 105.0:
                        already_engaged.append((d, enemy))
                    else:
                        enemy.reset_aggro()
                elif d <= 68.0 and enemy.stun_timer <= 0.0:
                    free_candidates.append((d, enemy))

            already_engaged.sort(key=lambda item: item[0])
            free_candidates.sort(key=lambda item: item[0])
            engaged_list = [item[1] for item in (already_engaged + free_candidates)[:max_engaged]]

            used_slots = set()
            need_slot = []
            for enemy in engaged_list:
                if enemy.is_engaged and enemy.combat_slot_index in (0, 1) and enemy.combat_slot_index not in used_slots:
                    used_slots.add(enemy.combat_slot_index)
                    enemy.total_engaged = len(engaged_list)
                else:
                    need_slot.append(enemy)

            for enemy in need_slot:
                if not enemy.is_engaged and floating_texts is not None:
                    floating_texts.add_status(enemy.x, enemy.y - 12, "!", (255, 75, 75))
                slot = 0 if 0 not in used_slots else 1
                used_slots.add(slot)
                enemy.engage_hero(hero, slot, len(engaged_list))

            # Всем остальным сбрасываем агр (продолжают идти по дороге)
            for enemy in self.enemies:
                if enemy not in engaged_list:
                    enemy.reset_aggro()
        else:
            for enemy in self.enemies:
                enemy.reset_aggro()

        # 3. Обновление живых врагов и нанесение урона Замку
        for enemy in self.enemies:
            enemy.update(
                eff_dt,
                hero=hero,
                particle_sys=particle_sys,
                floating_texts=floating_texts,
                wave_manager=self,
                cam_shake=cam_shake,
            )
            if enemy.reached_castle:
                # Враг прорвался в ворота цитадели!
                self.castle_hp = max(0, self.castle_hp - enemy.castle_damage)
                self.castle_flash_timer = 0.35
                if cam_shake:
                    cam_shake.add_trauma(0.35)
                if floating_texts:
                    floating_texts.add_status(VIRTUAL_WIDTH - 96, VIRTUAL_HEIGHT // 2 - 20, f"-{enemy.castle_damage} HP!", (255, 60, 60))

        # 3. Начисление золота и удаление достигших замка или завершивших анимацию смерти
        surviving_enemies = []
        for enemy in self.enemies:
            if enemy.reached_castle:
                continue
            if enemy.is_alive:
                surviving_enemies.append(enemy)
            else:
                if not getattr(enemy, "reward_claimed", False):
                    self.gold += enemy.reward_gold
                    self.total_enemies_killed += 1
                    enemy.reward_claimed = True
                if getattr(enemy, "is_dying", False) and not getattr(enemy, "death_finished", True):
                    surviving_enemies.append(enemy)

        self.enemies = surviving_enemies

        # 4. Проверка поражения
        if self.castle_hp <= 0:
            self.wave_state = "defeat"
            self.banner_title = "ПОРАЖЕНИЕ"
            self.banner_subtitle = "Цитадель Замка пала под натиском орды!"
            self.banner_timer = 999.0
            return

        # 5. Проверка завершения волны и победы
        if self.wave_state == "in_progress" and len(self.enemies) == 0:
            if self.current_wave >= self.total_waves:
                self.wave_state = "victory"
                self.banner_title = "ПОБЕДА!"
                self.banner_subtitle = "Все 10 волн отбиты, Королевство спасено!"
                self.banner_timer = 999.0
            else:
                self.wave_state = "completed"

    def draw_overlays(self, surface: pygame.Surface) -> None:
        """Отрисовывает вспышку урона по Замку и центральные информационные баннеры."""
        if self.castle_flash_timer > 0:
            flash_alpha = int(140 * (self.castle_flash_timer / 0.35))
            flash_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(flash_surf, (220, 30, 30, flash_alpha), (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT), 4)
            surface.blit(flash_surf, (0, 0))

        if self.banner_timer > 0:
            self._draw_wave_banner(surface)

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовывает всех врагов в Y-сортированном порядке и игровые баннеры."""
        for enemy in sorted(self.enemies, key=lambda e: e.y):
            enemy.draw(surface)
        self.draw_overlays(surface)

    def _draw_wave_banner(self, surface: pygame.Surface) -> None:
        """Отрисовывает стильный пергаментный баннер по центру экрана 960x720."""
        bw, bh = 380, 66
        bx = (VIRTUAL_WIDTH - bw) // 2
        by = 56

        # Полупрозрачная подложка
        banner_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        banner_surf.fill((24, 18, 14, 215))

        # Рамка с золотыми скосами
        is_gold = self.wave_state == "victory"
        border_col = (235, 195, 75) if is_gold else (165, 125, 65)
        pygame.draw.rect(banner_surf, border_col, (0, 0, bw, bh), 2)
        pygame.draw.rect(banner_surf, (45, 30, 20), (2, 2, bw - 4, bh - 4), 1)

        surface.blit(banner_surf, (bx, by))

        # Заголовок баннера
        t_col = (255, 225, 100) if is_gold else ((255, 70, 70) if self.wave_state == "defeat" else (255, 245, 225))
        shadow_col = (15, 10, 8)

        t_surf = self.font_title.render(self.banner_title, True, t_col)
        t_sh = self.font_title.render(self.banner_title, True, shadow_col)
        tx = bx + (bw - t_surf.get_width()) // 2
        surface.blit(t_sh, (tx + 2, by + 11))
        surface.blit(t_surf, (tx, by + 9))

        # Подзаголовок
        s_surf = self.font_sub.render(self.banner_subtitle, True, (215, 195, 165))
        s_sh = self.font_sub.render(self.banner_subtitle, True, shadow_col)
        sx = bx + (bw - s_surf.get_width()) // 2
        surface.blit(s_sh, (sx + 1, by + 43))
        surface.blit(s_surf, (sx, by + 42))
