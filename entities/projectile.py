"""
Модуль снарядов башен:
- Стрелы Башни лучников (PNG из assets/towers/archer/3 Units/Arrow/ с поворотом по вектору полёта)
- Магические сферы Башни магов (PNG из assets/towers/mage/3 Units/Projectiles/ со сплешем и замедлением)
"""

import math
from typing import List, Tuple, Optional, Callable
import pygame
from entities.enemy import Enemy
from core.assets import get_arrow_sprite, get_mage_projectile_sprite

_ORB_GLOW_COLORS = {
    1: (250, 210, 110),
    2: (235, 85, 95),
    3: (190, 105, 255),
}


class Projectile:
    """Снаряд, выпущенный башней по вражеской цели."""

    def __init__(
        self,
        start_pos: Tuple[float, float],
        target: Enemy,
        p_type: str = "arrow",
        damage: int = 14,
        splash_radius: float = 0.0,
        slow_ratio: float = 0.0,
        slow_duration: float = 0.0,
        ignore_armor: bool = False,
        proj_tier: int = 1,
        on_kill: Optional[Callable[[int, int], None]] = None,
    ):
        self.x, self.y = start_pos
        self.target = target
        self.target_last_pos = (target.x, target.y)
        self.p_type = p_type
        self.damage = damage
        self.splash_radius = splash_radius
        self.slow_ratio = slow_ratio
        self.slow_duration = slow_duration
        self.ignore_armor = ignore_armor
        self.proj_tier = proj_tier
        self.on_kill = on_kill

        self.speed = 265.0 if self.p_type == "magic_orb" else 380.0
        self.is_alive = True
        self.pulse_timer = 0.0

        dx = target.x - self.x
        dy = target.y - self.y
        self.angle = math.atan2(dy, dx)

    def update(
        self,
        dt: float,
        enemies: List[Enemy],
        particle_sys=None,
        floating_texts=None,
        cam_shake=None,
    ) -> None:
        """Перемещает снаряд к цели и обрабатывает попадание с запуском VFX."""
        if not self.is_alive:
            return

        self.pulse_timer += dt * 10.0

        if self.target.is_alive and not self.target.reached_castle:
            tx, ty = self.target.x, self.target.y
            self.target_last_pos = (tx, ty)
        else:
            tx, ty = self.target_last_pos

        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 0.001:
            self.angle = math.atan2(dy, dx)

        move_dist = self.speed * dt

        if dist <= move_dist or dist < 4.5:
            self.x, self.y = tx, ty
            self._hit(enemies, particle_sys, floating_texts, cam_shake)
            self.is_alive = False
        else:
            self.x += (dx / dist) * move_dist
            self.y += (dy / dist) * move_dist

    def _hit(
        self,
        enemies: List[Enemy],
        particle_sys=None,
        floating_texts=None,
        cam_shake=None,
    ) -> None:
        """Наносит прямой или сплеш-урон с замедлением и запускает VFX."""
        if self.splash_radius > 0.0:
            if particle_sys:
                particle_sys.add_magic_burst(self.x, self.y, radius=self.splash_radius)
            if cam_shake:
                cam_shake.add_trauma(0.10)

            for enemy in enemies:
                if enemy.is_alive and not enemy.reached_castle:
                    e_dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
                    if e_dist <= self.splash_radius:
                        falloff = 1.0 - (e_dist / self.splash_radius) * 0.4
                        effective_dmg = max(1, int(self.damage * falloff))
                        gold, xp = enemy.take_damage(effective_dmg, ignore_armor=self.ignore_armor)
                        if floating_texts:
                            floating_texts.add_damage(enemy.x, enemy.y, effective_dmg, is_critical=False)
                        if self.slow_ratio > 0.0:
                            enemy.apply_slow(self.slow_ratio, self.slow_duration)
                        if gold > 0 and self.on_kill:
                            enemy.reward_claimed = True
                            self._notify_kill(gold, xp, enemy.x, enemy.y)
                            if floating_texts:
                                floating_texts.add_gold(enemy.x, enemy.y - 12, gold)
        else:
            if self.target.is_alive and not self.target.reached_castle:
                gold, xp = self.target.take_damage(self.damage, ignore_armor=self.ignore_armor)
                if particle_sys:
                    particle_sys.add_hit_sparks(self.target.x, self.target.y, is_critical=False)
                if floating_texts:
                    floating_texts.add_damage(self.target.x, self.target.y, self.damage, is_critical=False)
                if self.slow_ratio > 0.0:
                    self.target.apply_slow(self.slow_ratio, self.slow_duration)
                if gold > 0 and self.on_kill:
                    self.target.reward_claimed = True
                    self._notify_kill(gold, xp, self.target.x, self.target.y)
                    if floating_texts:
                        floating_texts.add_gold(self.target.x, self.target.y - 12, gold)

    def _notify_kill(self, gold: int, xp: int, ex: float, ey: float) -> None:
        """Безопасно уведомляет о гибели врага от башни."""
        if not self.on_kill:
            return
        try:
            self.on_kill(gold, xp, ex, ey)
        except TypeError:
            self.on_kill(gold, xp)

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовывает PNG-стрелу или магический заряд из 3 Units/Projectiles/."""
        if not self.is_alive:
            return

        cx, cy = int(self.x), int(self.y)
        if self.p_type == "magic_orb":
            glow_col = _ORB_GLOW_COLORS.get(self.proj_tier, (190, 105, 255))
            r_glow = 6 + int(math.sin(self.pulse_timer) * 1.5)
            glow_surf = pygame.Surface((r_glow * 2 + 2, r_glow * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*glow_col, 95), (r_glow + 1, r_glow + 1), r_glow)
            surface.blit(glow_surf, (cx - r_glow - 1, cy - r_glow - 1))

            orb_surf = get_mage_projectile_sprite(self.proj_tier)
            surface.blit(orb_surf, (cx - orb_surf.get_width() // 2, cy - orb_surf.get_height() // 2))
        else:
            arrow_base = get_arrow_sprite()
            angle_deg = -math.degrees(self.angle)
            rotated = pygame.transform.rotate(arrow_base, angle_deg)
            rect = rotated.get_rect(center=(cx, cy))
            surface.blit(rotated, rect)
