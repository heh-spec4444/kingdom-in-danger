"""
Модуль героя-командира (Рыцарь-командир с PNG-спрайтами из assets/heroes/knight/).
Включает только базовую механику командира:
- Загрузку нарезанных PNG-анимаций idle (4 кадра), walk (6 кадров) и attack (4 кадра) 32x32 px
- Базовые характеристики (HP, урон, скорость атаки, скорость бега)
- Перемещение по сетке по ПКМ через поиск пути A* с обходом башен и препятствий
- Автобой в ближнем бою и агр врагов на линии
- Опыт (XP) и повышение уровня
- Гибель со штрафом золота и возрождение у ворот лагеря
"""

import math
from typing import List, Tuple, Optional
import pygame
from settings import (
    TILE_SIZE,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    HEROES,
    DEFAULT_HERO_ID,
    HERO_RESPAWN_TIME,
    HERO_RESPAWN_GOLD_PENALTY,
)
from core.pathfinding import find_path
from core.assets import get_font, get_hero_animations, get_hero_draw_metrics
from core.sound import play_sound


class Hero:
    """Управляет состоянием, анимациями, перемещением, автобоем и прокачкой уровня командира."""

    XP_THRESHOLDS = [60, 140, 240, 360, 500, 700, 950]

    def __init__(self, start_grid_pos: Tuple[int, int] = (35, 16), hero_id: Optional[str] = DEFAULT_HERO_ID):
        resolved_id = hero_id or DEFAULT_HERO_ID or "knight"
        self.hero_id = resolved_id
        hero_data = HEROES.get(resolved_id, {})

        self.name = hero_data.get("name", "Рыцарь-командир")
        self.title = hero_data.get("title", "Защитник короны")
        self.max_hp = int(hero_data.get("hp", 175))
        self.hp = float(self.max_hp)
        self.base_speed = float(hero_data.get("speed", 48.0))
        self.attack_damage = int(hero_data.get("attack_damage", 14))
        self.attack_range = float(hero_data.get("attack_range", 26.0))
        self.attack_cooldown = float(hero_data.get("attack_cooldown", 0.75))

        # Иконка портрета для HUD
        self.icon_card = "knight_card_3d"

        # Позиция в пикселях виртуального экрана (640x360)
        start_c, start_r = start_grid_pos
        self.start_x = float(MAP_OFFSET_X + start_c * TILE_SIZE + TILE_SIZE // 2)
        self.start_y = float(MAP_OFFSET_Y + start_r * TILE_SIZE + TILE_SIZE // 2)
        self.x = self.start_x
        self.y = self.start_y

        # Состояние жизни и возрождения
        self.is_alive = True
        self.respawn_timer = 0.0

        # Уровень и опыт
        self.level = 1
        self.xp = 0
        self.xp_to_next = self.XP_THRESHOLDS[0]

        # Боевые таймеры
        self.attack_timer = 0.0
        self.attack_anim_timer = 0.0
        self.attack_anim_duration = 0.32
        self.attack_combo_index = 0

        # Состояние движения и анимации
        self.state = "idle"
        self.facing_left = False
        self.anim_timer = 0.0
        self.anim_frame = 0

        # Загруженные и обрезанные PNG-анимации Tiny Swords с единой точкой опоры ног
        anims = get_hero_animations(self.hero_id)
        metrics = get_hero_draw_metrics(self.hero_id)
        self.foot_anchor_ratio = float(metrics.get("foot_ratio", 0.82))
        self.idle_frames: List[pygame.Surface] = list(anims.get("idle", []))
        self.walk_frames: List[pygame.Surface] = list(anims.get("walk", []))
        self.attack1_frames: List[pygame.Surface] = list(anims.get("attack1", anims.get("attack", [])))
        self.attack2_frames: List[pygame.Surface] = list(anims.get("attack2", self.attack1_frames))
        self.attack_variants: List[List[pygame.Surface]] = [
            v for v in (self.attack1_frames, self.attack2_frames) if v
        ]
        self.attack_frames: List[pygame.Surface] = (
            self.attack_variants[0] if self.attack_variants else []
        )

        # Маршрут перемещения A*
        self.waypoints: List[Tuple[float, float]] = []
        self.target_marker: Optional[Tuple[float, float]] = None
        self.marker_pulse = 0.0

    @property
    def current_speed(self) -> float:
        return self.base_speed

    @property
    def effective_damage(self) -> int:
        return self.attack_damage

    @property
    def effective_attack_cooldown(self) -> float:
        return self.attack_cooldown

    @property
    def grid_pos(self) -> Tuple[int, int]:
        c = int((self.x - MAP_OFFSET_X) // TILE_SIZE)
        r = int((self.y - MAP_OFFSET_Y) // TILE_SIZE)
        return c, r

    def set_destination(self, target_px: Tuple[int, int], game_map) -> bool:
        """Задаёт точку перемещения командира по ПКМ через A*."""
        if not self.is_alive:
            return False

        tx, ty = target_px
        col = (tx - MAP_OFFSET_X) // TILE_SIZE
        row = (ty - MAP_OFFSET_Y) // TILE_SIZE

        if not game_map.is_valid(col, row):
            return False

        cur_c, cur_r = self.grid_pos
        path_nodes = find_path(game_map, (cur_c, cur_r), (col, row))

        if not path_nodes or len(path_nodes) <= 1:
            if game_map.is_walkable(col, row):
                self.waypoints = [(float(tx), float(ty))]
                self.target_marker = (float(tx), float(ty))
                self.marker_pulse = 0.0
                self.state = "walk"
                return True
            return False

        self.waypoints = []
        for c, r in path_nodes[1:]:
            wx = float(MAP_OFFSET_X + c * TILE_SIZE + TILE_SIZE // 2)
            wy = float(MAP_OFFSET_Y + r * TILE_SIZE + TILE_SIZE // 2)
            self.waypoints.append((wx, wy))

        if path_nodes[-1] == (col, row):
            self.waypoints[-1] = (float(tx), float(ty))

        self.target_marker = (float(tx), float(ty))
        self.marker_pulse = 0.0
        self.state = "walk"
        if self.waypoints:
            first_dx = self.waypoints[0][0] - self.x
            if abs(first_dx) > 0.5:
                self.facing_left = first_dx < 0
        return True

    def move_to_pixel(self, tx: int, ty: int, game_map) -> bool:
        """Алиас для перемещения командира к пиксельным координатам."""
        return self.set_destination((tx, ty), game_map)

    def attack_enemy(
        self, enemy, particle_sys=None, floating_texts=None, cam_shake=None, wave_manager=None
    ) -> None:
        """Автоматическая атака мечом по ближайшему врагу (чередование Attack1 / Attack2)."""
        self.attack_timer = self.effective_attack_cooldown
        self.attack_anim_timer = self.attack_anim_duration
        if self.attack_variants:
            self.attack_frames = self.attack_variants[self.attack_combo_index % len(self.attack_variants)]
            self.attack_combo_index += 1
        self.facing_left = (enemy.x < self.x)
        dmg = self.effective_damage

        play_sound("sword_hit", 0.6)
        gold_reward, xp_reward = enemy.take_damage(dmg)
        if particle_sys:
            particle_sys.add_hit_sparks(enemy.x, enemy.y, is_critical=False)
        if floating_texts:
            floating_texts.add_damage(enemy.x, enemy.y, dmg, is_critical=False)

        if gold_reward > 0 and wave_manager:
            enemy.reward_claimed = True
            wave_manager.gold += gold_reward
            wave_manager.total_enemies_killed += 1
            if floating_texts:
                floating_texts.add_gold(enemy.x, enemy.y - 12, gold_reward)

        if xp_reward > 0:
            self.add_xp(xp_reward, particle_sys, floating_texts)
            if floating_texts:
                floating_texts.add_xp(enemy.x, enemy.y - 4, xp_reward)

    def take_damage(
        self,
        amount: int,
        particle_sys=None,
        floating_texts=None,
        wave_manager=None,
        cam_shake=None,
    ) -> None:
        """Получение прямого урона командиром."""
        if not self.is_alive:
            return

        dmg = max(1, int(amount))
        self.hp -= dmg

        if floating_texts:
            floating_texts.add_damage(self.x, self.y, dmg, is_critical=False)
        if particle_sys:
            particle_sys.add_hit_sparks(self.x, self.y, is_critical=False)

        if self.hp <= 0:
            self.hp = 0.0
            self.die(wave_manager, floating_texts, cam_shake)

    def die(self, wave_manager=None, floating_texts=None, cam_shake=None) -> None:
        """Гибель командира с 30% штрафом золота и таймером возрождения."""
        self.is_alive = False
        self.respawn_timer = HERO_RESPAWN_TIME
        self.waypoints.clear()
        self.target_marker = None
        self.state = "idle"
        play_sound("hero_death", 0.9)

        if cam_shake:
            cam_shake.add_trauma(0.4)
        if floating_texts:
            floating_texts.add_status(self.x, self.y - 12, "ГЕРОЙ ПАЛ!", (255, 65, 65))

        if wave_manager:
            penalty = int(wave_manager.gold * HERO_RESPAWN_GOLD_PENALTY)
            wave_manager.gold = max(0, wave_manager.gold - penalty)
            if floating_texts and penalty > 0:
                floating_texts.add_status(self.x, self.y + 4, f"-{penalty}g", (255, 120, 100))

    def respawn(self, particle_sys=None, floating_texts=None) -> None:
        """Возрождение командира у лагеря с полным запасом HP."""
        self.is_alive = True
        self.hp = float(self.max_hp)
        self.respawn_timer = 0.0
        self.x = self.start_x
        self.y = self.start_y
        self.state = "idle"
        self.waypoints.clear()
        self.target_marker = None

        if particle_sys:
            particle_sys.add_level_up_sparks(self.x, self.y)
        if floating_texts:
            floating_texts.add_status(self.x, self.y - 16, "ВОЗРОЖДЕНИЕ!", (120, 240, 140))

    def add_xp(self, amount: int, particle_sys=None, floating_texts=None) -> None:
        """Начисление опыта и повышение уровня командира."""
        if not self.is_alive:
            return
        self.xp += amount
        while self.level <= len(self.XP_THRESHOLDS) and self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.max_hp += 20
            self.hp = float(self.max_hp)
            self.attack_damage += 2
            idx = min(self.level - 1, len(self.XP_THRESHOLDS) - 1)
            self.xp_to_next = self.XP_THRESHOLDS[idx]
            play_sound("level_up", 0.85)

            if particle_sys:
                particle_sys.add_level_up_sparks(self.x, self.y)
            if floating_texts:
                floating_texts.add_status(self.x, self.y - 24, f"УРОВЕНЬ {self.level}!", (255, 230, 80))

    def update(
        self,
        dt: float,
        enemies=None,
        particle_sys=None,
        floating_texts=None,
        cam_shake=None,
        wave_manager=None,
    ) -> None:
        """Обновляет перемещение по A*, автобой ближнего боя и кадры анимации."""
        self.marker_pulse += dt * 5.0

        if not self.is_alive:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0.0:
                self.respawn(particle_sys, floating_texts)
            return

        if self.attack_timer > 0.0:
            self.attack_timer = max(0.0, self.attack_timer - dt)
        if self.attack_anim_timer > 0.0:
            self.attack_anim_timer = max(0.0, self.attack_anim_timer - dt)

        prev_state = self.state

        # Перемещение по маршруту A*
        if self.waypoints:
            self.state = "walk"
            target_x, target_y = self.waypoints[0]
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)

            move_dist = self.current_speed * dt
            if dist <= move_dist or dist < 2.0:
                self.x = target_x
                self.y = target_y
                self.waypoints.pop(0)
                if not self.waypoints:
                    self.state = "idle"
                    self.target_marker = None
            else:
                self.x += (dx / dist) * move_dist
                self.y += (dy / dist) * move_dist
                if abs(dx) > 0.5:
                    self.facing_left = (dx < 0)
        else:
            self.state = "idle"
            self.target_marker = None

        if self.state != prev_state:
            self.anim_timer = 0.0
            self.anim_frame = 0

        # Автобой: атака ближайшего врага в радиусе ближнего боя
        if enemies and self.attack_timer <= 0.0:
            closest_enemy = None
            min_dist = self.attack_range
            for enemy in enemies:
                if not enemy.is_alive:
                    continue
                d = math.hypot(enemy.x - self.x, enemy.y - self.y)
                if d <= min_dist:
                    min_dist = d
                    closest_enemy = enemy

            if closest_enemy is not None:
                self.attack_enemy(
                    closest_enemy,
                    particle_sys=particle_sys,
                    floating_texts=floating_texts,
                    cam_shake=cam_shake,
                    wave_manager=wave_manager,
                )

        # Обновление кадра анимации
        anim_speed = 0.09 if self.state == "walk" else 0.14
        frames = self.walk_frames if self.state == "walk" else self.idle_frames
        max_f = max(1, len(frames))
        self.anim_timer += dt
        if self.anim_timer >= anim_speed:
            self.anim_timer = 0.0
            self.anim_frame = (self.anim_frame + 1) % max_f

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовывает линию пути, маркер цели, спрайт Рыцаря и полоску HP с единой привязкой ног."""
        if not self.is_alive:
            tx, ty = int(self.x), int(self.y)
            pygame.draw.ellipse(surface, (15, 30, 18, 120), (tx - 10, ty + 4, 20, 6))
            pygame.draw.line(surface, (200, 215, 235), (tx, ty - 12), (tx, ty + 4), 2)
            pygame.draw.line(surface, (255, 215, 60), (tx - 4, ty - 7), (tx + 4, ty - 7), 2)
            secs_left = int(math.ceil(self.respawn_timer))
            f = get_font(10)
            txt = f.render(f"{secs_left}s", True, (255, 225, 90))
            surface.blit(txt, (tx - txt.get_width() // 2, ty - 24))
            return

        # 1. Пунктирная линия запланированного пути
        if self.waypoints:
            pts = [(int(self.x), int(self.y))] + [(int(wx), int(wy)) for wx, wy in self.waypoints]
            for i in range(len(pts) - 1):
                self._draw_dashed_line(surface, pts[i], pts[i + 1])

        # 2. Пульсирующая метка цели ПКМ
        if self.target_marker:
            mx, my = int(self.target_marker[0]), int(self.target_marker[1])
            pulse = math.sin(self.marker_pulse) * 2.5
            r = int(8 + pulse)
            diamond_pts = [(mx, my - r), (mx + r, my), (mx, my + r), (mx - r, my)]
            pygame.draw.polygon(surface, (255, 225, 75), diamond_pts, 1)
            pygame.draw.circle(surface, (120, 240, 140), (mx, my), 3)

        # 3. Выбор кадра анимации (attack1/attack2 -> walk -> idle)
        if self.attack_anim_timer > 0.0 and self.attack_frames:
            progress = 1.0 - (self.attack_anim_timer / max(0.01, self.attack_anim_duration))
            atk_idx = min(len(self.attack_frames) - 1, max(0, int(progress * len(self.attack_frames))))
            current_frame = self.attack_frames[atk_idx]
        elif self.state == "walk" and self.walk_frames:
            current_frame = self.walk_frames[self.anim_frame % len(self.walk_frames)]
        elif self.idle_frames:
            current_frame = self.idle_frames[self.anim_frame % len(self.idle_frames)]
        else:
            return

        if self.facing_left:
            current_frame = pygame.transform.flip(current_frame, True, False)

        # Единая привязка по центру и линии ног без скачков между Idle/Run/Attack
        foot_y_px = round(current_frame.get_height() * self.foot_anchor_ratio)
        draw_x = round(self.x) - current_frame.get_width() // 2
        draw_y = round(self.y) + 6 - foot_y_px
        surface.blit(current_frame, (draw_x, draw_y))

        # 4. Аккуратная полоска HP над головой
        hp_w, hp_h = 28, 4
        hp_x = round(self.x) - hp_w // 2
        hp_y = draw_y - 2
        hp_ratio = max(0.0, min(1.0, self.hp / self.max_hp))
        fill_w = int(hp_w * hp_ratio)

        pygame.draw.rect(surface, (30, 27, 24), (hp_x - 1, hp_y - 1, hp_w + 2, hp_h + 2))
        pygame.draw.rect(surface, (200, 45, 45), (hp_x, hp_y, hp_w, hp_h))
        pygame.draw.rect(surface, (55, 215, 75), (hp_x, hp_y, fill_w, hp_h))

    def _draw_dashed_line(
        self, surface: pygame.Surface, p1: Tuple[int, int], p2: Tuple[int, int]
    ) -> None:
        """Отрисовывает пунктирную линию пути между двумя точками."""
        x1, y1 = p1
        x2, y2 = p2
        dist = math.hypot(x2 - x1, y2 - y1)
        if dist < 1.0:
            return

        step = 5.0
        num_steps = int(dist // step)
        dx = (x2 - x1) / dist
        dy = (y2 - y1) / dist

        for s in range(0, num_steps, 2):
            px = int(x1 + dx * s * step)
            py = int(y1 + dy * s * step)
            surface.set_at((px, py), (255, 230, 90))
            if s % 4 == 0:
                surface.set_at((px + 1, py), (140, 220, 255))
