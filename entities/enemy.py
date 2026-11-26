"""
Модуль вражеских сущностей: Слизень, Пчела, Гоблин с дубиной и Волк.
Использует только PNG-спрайты из assets/enemies/ (D/S/U, Walk, Attack, Death):
- 6-кадровые анимации ходьбы, атаки (или рывка для Слизня/Пчелы) и смерти
- Автовыбор направления (D/U/S) и зеркальное отражение вправо для боковых спрайтов
- Единая привязка по центру и линии опоры
- Полоска HP над головой, золотая корона вожаков/боссов, эффекты оглушения и замедления
"""

import math
from typing import List, Tuple, Dict, Optional
import pygame
from settings import (
    ENEMIES,
    WAVE_HP_SCALE,
    WAVE_REWARD_SCALE,
)
from core.assets import get_enemy_animations, get_enemy_draw_metrics

_ANIM_FRAME_DURATIONS: Dict[str, float] = {
    "bee": 0.07,
    "wolf": 0.08,
    "goblin": 0.10,
    "slime": 0.11,
}


class Enemy:
    """Сущность врага, наступающего по дороге к Командному лагерю."""

    MELEE_SLOT_RADIUS = 25.0
    MELEE_STOP_DEADZONE = 3.0
    MELEE_RECHASE_DIST = 9.0
    MELEE_ATTACK_RANGE = 36.0

    def __init__(
        self,
        enemy_type: str,
        waypoints: List[Tuple[float, float]],
        wave_index: int = 0,
        is_boss: bool = False,
        spawn_x: Optional[float] = None,
        spawn_y: Optional[float] = None,
    ):
        self.enemy_type = enemy_type if enemy_type in ENEMIES else "slime"
        self.is_boss = bool(is_boss)
        self.wave_index = wave_index

        data = ENEMIES[self.enemy_type]
        self.name = str(data["name"])
        if self.is_boss and self.enemy_type == "goblin":
            self.name = "Король гоблинов" if wave_index >= 9 else "Вожак гоблинов"

        # Масштабирование сложности от номера волны и статуса босса
        hp_mult = 1.0 + wave_index * WAVE_HP_SCALE
        if self.is_boss:
            hp_mult *= (3.2 if wave_index >= 9 else 1.9)
        reward_mult = (1.0 + wave_index * WAVE_REWARD_SCALE) * (2.5 if self.is_boss else 1.0)

        self.max_hp = max(1, int(data["hp"] * hp_mult))
        self.hp = self.max_hp
        self.base_speed = float(data["speed"]) * (0.90 if self.is_boss else 1.0)
        self.speed = self.base_speed
        self.slow_ratio = 0.0
        self.slow_timer = 0.0
        self.stun_timer = 0.0
        self.flash_timer = 0.0

        self.attack_timer = 0.0
        self.attack_cooldown = 1.0
        self.attack_damage = int(data.get("attack_damage", 8) * (1.6 if self.is_boss else 1.0))
        self.attack_anim_timer = 0.0
        self.attack_anim_duration = 0.36
        self.lunge_dx = 0.0
        self.lunge_dy = 0.0

        self.reward_gold = max(1, int(data["reward_gold"] * reward_mult))
        self.reward_xp = max(1, int(data["reward_xp"] * reward_mult))
        self.castle_damage = int(data["castle_damage"] * (2 if self.is_boss else 1))
        self.armor = float(data.get("armor", 0.0)) + (0.10 if self.is_boss else 0.0)
        self.width, self.height = data.get("size", (28, 28))

        self.is_engaged = False
        self.combat_slot_index = -1
        self.total_engaged = 1
        self.combat_offset: Optional[Tuple[float, float]] = None
        self.in_melee_stance = False

        # Маршрут по точкам дороги
        self.waypoints = list(waypoints)
        self.current_wp_idx = 0

        if spawn_x is not None and spawn_y is not None:
            self.x, self.y = float(spawn_x), float(spawn_y)
        elif self.waypoints:
            self.x, self.y = float(self.waypoints[0][0]), float(self.waypoints[0][1])
        else:
            self.x, self.y = 0.0, 0.0

        # Состояние жизни, смерти и PNG-анимаций
        self.is_alive = True
        self.is_dying = False
        self.death_timer = 0.0
        self.death_duration = 0.48
        self.death_finished = False
        self.reward_claimed = False
        self.reached_castle = False

        # D (вниз), U (вверх), S (вбок; в PNG смотрит влево -> при facing_left=False отражаем вправо)
        self.dir_key = "S"
        self.facing_left = False
        self.anim_timer = 0.0
        self.anim_frame = 0

        self.anims = get_enemy_animations(self.enemy_type, self.is_boss)
        self.metrics = get_enemy_draw_metrics(self.enemy_type, self.is_boss)
        self.foot_ratio = float(self.metrics.get("foot_ratio", 0.82))
        self.head_ratio = float(self.metrics.get("head_ratio", 0.10))
        self.has_native_attack = bool(self.metrics.get("has_native_attack", False))

        # Эффекты периодического урона (DoT)
        self.burn_timer = 0.0
        self.burn_dps = 0.0
        self.burn_tick_acc = 0.0

    @property
    def frames(self) -> List[pygame.Surface]:
        """Возвращает кадры текущей активной анимации и направления."""
        if self.is_dying:
            anim_key = "death"
        elif self.attack_anim_timer > 0.0:
            anim_key = "attack"
        else:
            anim_key = "walk"
        dir_map = self.anims.get(anim_key) or self.anims.get("walk", {})
        return dir_map.get(self.dir_key) or dir_map.get("S", [])

    def _update_facing(self, dx: float, dy: float) -> None:
        """Обновляет направление спрайта (D/U/S) и разворот влево/вправо."""
        if abs(dx) >= abs(dy):
            self.dir_key = "S"
            if abs(dx) > 0.2:
                self.facing_left = (dx < 0)
        else:
            self.dir_key = "D" if dy > 0 else "U"
            if abs(dx) > 0.5:
                self.facing_left = (dx < 0)

    def engage_hero(self, hero, slot_index: int = 0, total_engaged: int = 1) -> None:
        """Фиксирует статичный слот боя по бокам/спереди от героя без вращения по кругу."""
        self.is_engaged = True
        self.combat_slot_index = slot_index
        self.total_engaged = total_engaged
        self.in_melee_stance = False

        vx = self.x - hero.x
        vy = self.y - hero.y
        if abs(vx) >= abs(vy):
            base_angle = math.pi if vx <= 0 else 0.0
        else:
            base_angle = -math.pi * 0.5 if vy < 0 else math.pi * 0.5

        spread = -0.52 if (slot_index % 2 == 0) else 0.52
        slot_angle = base_angle + spread
        self.combat_offset = (
            math.cos(slot_angle) * self.MELEE_SLOT_RADIUS,
            math.sin(slot_angle) * self.MELEE_SLOT_RADIUS,
        )

    def reset_aggro(self) -> None:
        """Сбрасывает агр и очищает зафиксированный слот ближнего боя."""
        self.is_engaged = False
        self.combat_slot_index = -1
        self.combat_offset = None
        self.in_melee_stance = False

    def _begin_death(self) -> None:
        """Запускает анимацию смерти врага без сдвига координат."""
        self.is_alive = False
        self.is_dying = True
        self.reset_aggro()
        self.death_timer = 0.0
        self.death_finished = False
        self.attack_anim_timer = 0.0

    def take_damage(self, amount: int, ignore_armor: bool = False) -> Tuple[int, int]:
        """Наносит врагу урон; при гибели запускает анимацию смерти и возвращает (gold, xp)."""
        if not self.is_alive:
            return 0, 0

        self.flash_timer = 0.12
        effective_dmg = amount if ignore_armor else max(1, int(amount * (1.0 - self.armor)))
        self.hp -= effective_dmg

        if self.hp <= 0:
            self.hp = 0
            self._begin_death()
            return self.reward_gold, self.reward_xp

        return 0, 0

    def apply_stun(self, duration: float) -> None:
        """Оглушает врага на указанное время."""
        if not self.is_alive:
            return
        self.stun_timer = max(self.stun_timer, duration)

    def apply_slow(self, ratio: float, duration: float) -> None:
        """Накладывает замедление от магической башни."""
        if not self.is_alive:
            return
        if ratio >= self.slow_ratio or duration > self.slow_timer:
            self.slow_ratio = max(self.slow_ratio, ratio)
            self.slow_timer = max(self.slow_timer, duration)
            self.speed = self.base_speed * (1.0 - self.slow_ratio)

    def apply_burn(self, dps: float, duration: float) -> None:
        """Накладывает эффект горения (DoT)."""
        if not self.is_alive:
            return
        self.burn_timer = max(self.burn_timer, duration)
        self.burn_dps = max(self.burn_dps, dps)

    def _advance_walk_anim(self, dt: float) -> None:
        frame_dur = _ANIM_FRAME_DURATIONS.get(self.enemy_type, 0.10)
        cur_frames = self.frames
        if not cur_frames:
            return
        self.anim_timer += dt
        if self.anim_timer >= frame_dur:
            self.anim_timer = 0.0
            self.anim_frame = (self.anim_frame + 1) % len(cur_frames)

    def update(
        self,
        dt: float,
        hero=None,
        particle_sys=None,
        floating_texts=None,
        wave_manager=None,
        cam_shake=None,
    ) -> None:
        """Обновляет состояние, перемещение по маршруту, бой с командиром и анимации."""
        if self.reached_castle:
            return

        if self.is_dying:
            self.death_timer += dt
            if self.death_timer >= self.death_duration:
                self.death_finished = True
            return

        if not self.is_alive:
            return

        # Обновление периодического урона (DoT)
        if self.burn_timer > 0.0:
            self.burn_timer = max(0.0, self.burn_timer - dt)
            self.burn_tick_acc += dt
            if self.burn_tick_acc >= 0.5:
                self.burn_tick_acc -= 0.5
                tick_dmg = max(1, int(self.burn_dps * 0.5))
                gold_r, xp_r = self.take_damage(tick_dmg, ignore_armor=True)
                if particle_sys and hasattr(particle_sys, "add_burn_tick"):
                    particle_sys.add_burn_tick(self.x, self.y)
                if floating_texts:
                    floating_texts.add_damage(self.x, self.y, tick_dmg, is_critical=False)
                if gold_r > 0 and wave_manager:
                    wave_manager.gold += gold_r
                    wave_manager.total_enemies_killed += 1
                    self.reward_claimed = True
                    if floating_texts:
                        floating_texts.add_gold(self.x, self.y - 12, gold_r)
                if xp_r > 0 and hero and getattr(hero, "is_alive", False):
                    hero.add_xp(xp_r, particle_sys, floating_texts)
                if not self.is_alive:
                    return

        if self.flash_timer > 0.0:
            self.flash_timer = max(0.0, self.flash_timer - dt)
        if self.attack_timer > 0.0:
            self.attack_timer = max(0.0, self.attack_timer - dt)
        if self.attack_anim_timer > 0.0:
            self.attack_anim_timer = max(0.0, self.attack_anim_timer - dt)

        if self.stun_timer > 0.0:
            self.stun_timer = max(0.0, self.stun_timer - dt)
            return

        # Автономный агр на героя при запуске без wave_manager
        if wave_manager is None and hero is not None:
            d_hero = math.hypot(self.x - hero.x, self.y - hero.y)
            if self.is_engaged:
                if d_hero > 105.0 or not hero.is_alive:
                    self.reset_aggro()
            elif d_hero <= 68.0 and hero.is_alive and self.stun_timer <= 0.0:
                self.engage_hero(hero, slot_index=0, total_engaged=1)

        # Поведение в бою с командиром: движение к статичному слоту и остановка на месте
        if self.is_engaged and hero is not None and hero.is_alive:
            if self.combat_offset is None:
                self.engage_hero(hero, max(0, self.combat_slot_index), self.total_engaged)

            ox, oy = self.combat_offset
            target_x = hero.x + ox
            target_y = hero.y + oy

            dx = target_x - self.x
            dy = target_y - self.y
            dist_to_slot = math.hypot(dx, dy)

            if self.in_melee_stance:
                if dist_to_slot > self.MELEE_RECHASE_DIST:
                    self.in_melee_stance = False
            else:
                move_dist = self.speed * dt
                if dist_to_slot <= self.MELEE_STOP_DEADZONE:
                    self.in_melee_stance = True
                elif dist_to_slot <= move_dist:
                    self.x = target_x
                    self.y = target_y
                    self.in_melee_stance = True
                else:
                    self.x += (dx / dist_to_slot) * move_dist
                    self.y += (dy / dist_to_slot) * move_dist

            mdx = hero.x - self.x
            mdy = hero.y - self.y
            self._update_facing(mdx, mdy)

            dist_hero = math.hypot(mdx, mdy)
            if dist_hero <= self.MELEE_ATTACK_RANGE and self.attack_timer <= 0.0:
                self.attack_timer = self.attack_cooldown
                self.attack_anim_timer = self.attack_anim_duration
                if dist_hero > 0.5:
                    self.lunge_dx = mdx / dist_hero
                    self.lunge_dy = mdy / dist_hero
                else:
                    self.lunge_dx, self.lunge_dy = (-1.0 if self.facing_left else 1.0), 0.0

                hero.take_damage(
                    self.attack_damage,
                    particle_sys=particle_sys,
                    floating_texts=floating_texts,
                    wave_manager=wave_manager,
                    cam_shake=cam_shake,
                )

            if not self.in_melee_stance or self.enemy_type == "bee":
                self._advance_walk_anim(dt)
            else:
                self.anim_frame = 0
                self.anim_timer = 0.0
            return

        # Обновление замедления
        if self.slow_timer > 0.0:
            self.slow_timer = max(0.0, self.slow_timer - dt)
            if self.slow_timer <= 0.0:
                self.slow_ratio = 0.0
                self.speed = self.base_speed
            else:
                self.speed = self.base_speed * (1.0 - self.slow_ratio)

        if self.current_wp_idx >= len(self.waypoints):
            self.reached_castle = True
            self.is_alive = False
            return

        target_x, target_y = self.waypoints[self.current_wp_idx]
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        move_dist = self.speed * dt

        if dist <= move_dist or dist < 1.5:
            self.x = target_x
            self.y = target_y
            self.current_wp_idx += 1
            if self.current_wp_idx >= len(self.waypoints):
                self.reached_castle = True
                self.is_alive = False
        else:
            self.x += (dx / dist) * move_dist
            self.y += (dy / dist) * move_dist
            self._update_facing(dx, dy)

        self._advance_walk_anim(dt)

    def _select_draw_frame(self) -> Tuple[Optional[pygame.Surface], int, int]:
        """Выбирает кадр спрайта с учётом смерти/атаки/ходьбы, разворота и рывка."""
        if self.is_dying:
            frames = self.anims.get("death", {}).get(self.dir_key) or self.frames
            if not frames:
                return None, 0, 0
            prog = min(1.0, max(0.0, self.death_timer / max(0.01, self.death_duration)))
            idx = min(len(frames) - 1, int(prog * len(frames)))
            return frames[idx], 0, 0

        lunge_x, lunge_y = 0, 0
        if self.attack_anim_timer > 0.0:
            frames = self.anims.get("attack", {}).get(self.dir_key) or self.frames
            if not frames:
                return None, 0, 0
            prog = 1.0 - (self.attack_anim_timer / max(0.01, self.attack_anim_duration))
            idx = min(len(frames) - 1, max(0, int(prog * len(frames))))
            pulse = math.sin(prog * math.pi)
            amp = 6.0 if not self.has_native_attack else 2.5
            lunge_x = round(self.lunge_dx * amp * pulse)
            lunge_y = round(self.lunge_dy * amp * pulse)
            return frames[idx], lunge_x, lunge_y

        frames = self.anims.get("walk", {}).get(self.dir_key) or self.frames
        if not frames:
            return None, 0, 0
        return frames[self.anim_frame % len(frames)], 0, 0

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовывает PNG-спрайт врага, тень замедления, полоску HP и корону босса."""
        if self.reached_castle or (not self.is_alive and not self.is_dying) or self.death_finished:
            return

        frame, lunge_x, lunge_y = self._select_draw_frame()
        if frame is None:
            return

        # Боковые спрайты (S_*) смотрят влево — отражаем при движении/ударе вправо
        if self.dir_key == "S" and not self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        foot_y_px = round(frame.get_height() * self.foot_ratio)
        head_y_offset = round(frame.get_height() * self.head_ratio)
        draw_x = round(self.x) - frame.get_width() // 2 + lunge_x
        draw_y = round(self.y) + 6 - foot_y_px + lunge_y

        # Эффект заморозки под ногами живого врага
        if self.is_alive and self.slow_timer > 0.0:
            ice_w = max(20, int(self.width) + 4)
            pygame.draw.ellipse(
                surface, (80, 180, 245, 130),
                (round(self.x) - ice_w // 2, draw_y + foot_y_px - 2, ice_w, 4),
            )

        if self.flash_timer > 0.0 and self.is_alive:
            flash_surf = frame.copy()
            flash_surf.fill((200, 200, 200, 0), special_flags=pygame.BLEND_RGBA_ADD)
            surface.blit(flash_surf, (draw_x, draw_y))
        else:
            surface.blit(frame, (draw_x, draw_y))

        if not self.is_alive:
            return

        if self.slow_timer > 0.0:
            surface.set_at((round(self.x) - 2, round(self.y) - 2), (180, 235, 255))
            surface.set_at((round(self.x) + 3, round(self.y) + 1), (130, 210, 255))

        # --- Полоска HP над головой ---
        bar_w = 34 if self.is_boss else (28 if self.enemy_type in ("goblin", "wolf") else 22)
        bar_h = 4
        bar_x = round(self.x) - bar_w // 2
        bar_y = draw_y + head_y_offset - 6

        pygame.draw.rect(surface, (20, 12, 10), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(surface, (50, 20, 20), (bar_x, bar_y, bar_w, bar_h))

        fill_ratio = max(0.0, min(1.0, self.hp / max(1, self.max_hp)))
        fill_w = int(bar_w * fill_ratio)
        if fill_w > 0:
            hp_color = (255, 175, 45) if self.is_boss else (255, 60, 60)
            pygame.draw.rect(surface, hp_color, (bar_x, bar_y, fill_w, bar_h))

        # Золотая корона для вожака/босса волн 5 и 10
        if self.is_boss:
            cx = round(self.x)
            cy = bar_y - 3
            pygame.draw.polygon(surface, (255, 215, 55), [
                (cx - 5, cy + 2),
                (cx - 5, cy - 3),
                (cx - 2, cy),
                (cx, cy - 4),
                (cx + 2, cy),
                (cx + 5, cy - 3),
                (cx + 5, cy + 2),
            ])

        # Звёздочки оглушения
        if self.stun_timer > 0.0:
            star_time = pygame.time.get_ticks() * 0.008
            star_cy = bar_y - (9 if self.is_boss else 4)
            for s_idx in range(3):
                s_ang = star_time + (s_idx * (math.pi * 2 / 3))
                sx = round(self.x + math.cos(s_ang) * 7)
                sy = round(star_cy + math.sin(s_ang) * 2.5)
                surface.set_at((sx, sy), (255, 255, 255))
                surface.set_at((sx - 1, sy), (255, 225, 60))
                surface.set_at((sx + 1, sy), (255, 225, 60))
                surface.set_at((sx, sy - 1), (255, 225, 60))
                surface.set_at((sx, sy + 1), (255, 225, 60))
