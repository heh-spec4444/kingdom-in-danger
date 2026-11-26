"""
Модуль системы пиксельных визуальных эффектов (VFX):
- Искры ударов и брызги в бою
- Дуга клинка для «Вихря клинков» [Q]
- Золотая ударная волна для «Боевого клича» [W]
- Магические взрывы и замедляющие снежинки
- Золотые фонтаны при повышении уровня (Level Up)
"""

import math
import random
from typing import List, Tuple
import pygame


class Particle:
    """Одиночная пиксельная частица."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: Tuple[int, int, int],
        lifetime: float,
        size: float = 2.0,
        gravity: float = 0.0,
        fade: bool = True,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.gravity = gravity
        self.fade = fade
        self.is_alive = True

    def update(self, dt: float) -> None:
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_alive = False
            return

        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface: pygame.Surface) -> None:
        if not self.is_alive:
            return

        ratio = max(0.0, self.lifetime / self.max_lifetime)
        cur_size = max(1, int(self.size * (ratio if self.fade else 1.0)))

        draw_x = int(self.x)
        draw_y = int(self.y)

        if cur_size == 1:
            surface.set_at((draw_x, draw_y), self.color)
        else:
            pygame.draw.rect(surface, self.color, (draw_x, draw_y, cur_size, cur_size))


class ShockwaveRing:
    """Расширяющееся кольцо ударной волны (для «Боевого клича» или взрывов)."""

    def __init__(
        self,
        x: float,
        y: float,
        max_radius: float,
        color: Tuple[int, int, int],
        duration: float = 0.4,
    ):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.color = color
        self.duration = duration
        self.timer = 0.0
        self.is_alive = True

    def update(self, dt: float) -> None:
        self.timer += dt
        if self.timer >= self.duration:
            self.is_alive = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.is_alive:
            return

        progress = self.timer / self.duration
        r = int(self.max_radius * progress)
        if r < 2:
            return

        alpha = int(220 * (1.0 - progress))
        ring_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        col = (self.color[0], self.color[1], self.color[2], alpha)
        pygame.draw.circle(ring_surf, col, (r + 1, r + 1), r, 2)
        surface.blit(ring_surf, (int(self.x - r - 1), int(self.y - r - 1)))


class WhirlwindEffect:
    """Визуальная вращающаяся дуга клинка для навыка [Q] «Вихрь клинков»."""

    def __init__(self, x: float, y: float, radius: float = 40.0, duration: float = 0.45):
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration
        self.timer = 0.0
        self.is_alive = True

    def update(self, dt: float) -> None:
        self.timer += dt
        if self.timer >= self.duration:
            self.is_alive = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.is_alive:
            return

        progress = self.timer / self.duration
        # Дуга клинка совершает полный оборот 360 градусов
        angle_base = progress * math.pi * 4.0
        alpha = int(230 * (1.0 - progress))

        r = int(self.radius)
        w_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        cx, cy = r + 2, r + 2

        # Двойная стальная и белая режущая полоса
        for i in range(12):
            ang = angle_base - (i * 0.15)
            cur_r = self.radius * (0.8 + 0.2 * math.cos(ang * 0.5))
            px = cx + int(cur_r * math.cos(ang))
            py = cy + int(cur_r * math.sin(ang) * 0.7)  # Эллипс в 2.5D проекции

            col = (255, 255, 255, max(0, alpha - i * 15)) if i < 4 else (180, 210, 245, max(0, alpha - i * 18))
            pygame.draw.circle(w_surf, col, (px, py), 2 if i < 5 else 1)

        surface.blit(w_surf, (int(self.x - cx), int(self.y - cy)))


class ParticleSystem:
    """Централизованный менеджер всех частиц и спецэффектов."""

    def __init__(self):
        self.particles: List[Particle] = []
        self.shockwaves: List[ShockwaveRing] = []
        self.whirlwinds: List[WhirlwindEffect] = []

    def clear(self) -> None:
        self.particles.clear()
        self.shockwaves.clear()
        self.whirlwinds.clear()

    def add_hit_sparks(self, x: float, y: float, is_critical: bool = False) -> None:
        """Искры от удара мечом или попадания стрелы/болта."""
        count = 10 if is_critical else 6
        colors = [(255, 230, 80), (255, 175, 40), (240, 245, 255)] if is_critical else [(220, 180, 60), (200, 210, 225)]
        for _ in range(count):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(30, 90 if is_critical else 60)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 20
            color = random.choice(colors)
            self.particles.append(Particle(x, y, vx, vy, color, lifetime=random.uniform(0.2, 0.4), size=2, gravity=140))

    def add_whirlwind(self, x: float, y: float, radius: float = 40.0) -> None:
        """Запуск эффекта «Вихрь клинков»."""
        self.whirlwinds.append(WhirlwindEffect(x, y, radius=radius))
        # Разлетающиеся стальные искры
        for _ in range(16):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(40, 110)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd * 0.7
            self.particles.append(Particle(x, y, vx, vy, (230, 240, 255), lifetime=random.uniform(0.25, 0.45), size=2))

    def add_warcry(self, x: float, y: float, radius: float = 55.0) -> None:
        """Золотая звуковая волна от «Боевого клича»."""
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=radius, color=(255, 215, 60), duration=0.45))
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=radius * 0.7, color=(255, 240, 150), duration=0.35))

    def add_magic_burst(self, x: float, y: float, radius: float = 35.0) -> None:
        """Астральный магический взрыв со сплешем."""
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=radius, color=(175, 95, 255), duration=0.35))
        for _ in range(14):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(30, 85)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            col = random.choice([(195, 115, 255), (130, 220, 255), (255, 255, 255)])
            self.particles.append(Particle(x, y, vx, vy, col, lifetime=random.uniform(0.25, 0.5), size=2))

    def add_level_up_sparks(self, x: float, y: float) -> None:
        """Золотые искры при повышении уровня командира."""
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=32.0, color=(255, 225, 80), duration=0.6))
        for _ in range(24):
            ang = random.uniform(-math.pi * 0.8, -math.pi * 0.2)
            spd = random.uniform(50, 120)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            col = random.choice([(255, 235, 90), (255, 205, 50), (255, 255, 255)])
            self.particles.append(Particle(x, y, vx, vy, col, lifetime=random.uniform(0.4, 0.7), size=2, gravity=90))

    def add_fire_wave(self, x: float, y: float, facing_left: bool = False, radius: float = 65.0) -> None:
        """Огненная волна [Q] Пироманта: конус пламени и взрывные частицы."""
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=radius, color=(255, 95, 20), duration=0.4))
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=radius * 0.6, color=(255, 220, 60), duration=0.3))
        dir_mult = -1.0 if facing_left else 1.0
        for _ in range(28):
            ang = random.uniform(-0.85, 0.85) if dir_mult > 0 else random.uniform(math.pi - 0.85, math.pi + 0.85)
            spd = random.uniform(60, 150)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            col = random.choice([(255, 45, 15), (255, 140, 25), (255, 235, 85), (255, 255, 200)])
            self.particles.append(Particle(x, y, vx, vy, col, lifetime=random.uniform(0.25, 0.5), size=random.choice([2, 3])))

    def add_flame_shield(self, x: float, y: float, radius: float = 36.0) -> None:
        """Пылающая огненная аура [W] Пироманта."""
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=radius, color=(255, 125, 30), duration=0.35))
        for _ in range(16):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(25, 60)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            col = random.choice([(255, 60, 20), (255, 175, 40), (255, 240, 110)])
            self.particles.append(Particle(x, y, vx, vy, col, lifetime=random.uniform(0.3, 0.55), size=2))

    def add_arrow_rain(self, x: float, y: float, radius: float = 45.0) -> None:
        """Град стрел [Q] Следопыта: дождь стрел с неба и брызги земли."""
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=radius, color=(220, 240, 255), duration=0.4))
        # Падающие сверху стрелы
        for _ in range(22):
            rx = x + random.uniform(-radius, radius)
            ry = y + random.uniform(-radius * 0.6, radius * 0.6)
            start_y = ry - random.uniform(70, 120)
            vx = random.uniform(-15, 15)
            vy = random.uniform(240, 320)
            col = random.choice([(235, 245, 255), (200, 215, 235), (255, 235, 120)])
            self.particles.append(Particle(rx, start_y, vx, vy, col, lifetime=0.32, size=2, fade=False))
            # Искры от удара о землю
            self.particles.append(Particle(rx, ry, random.uniform(-30, 30), random.uniform(-40, -10), (245, 215, 120), lifetime=0.25, size=2, gravity=120))

    def add_spike_trap(self, x: float, y: float) -> None:
        """Срабатывание ловушки с шипами [W] Следопыта."""
        self.shockwaves.append(ShockwaveRing(x, y, max_radius=30.0, color=(190, 205, 225), duration=0.3))
        for _ in range(16):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(40, 95)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 25
            col = random.choice([(235, 240, 255), (145, 160, 180), (255, 210, 75)])
            self.particles.append(Particle(x, y, vx, vy, col, lifetime=random.uniform(0.2, 0.4), size=2, gravity=130))

    def add_burn_tick(self, x: float, y: float) -> None:
        """Микро-вспышка огня при тике ожога."""
        for _ in range(4):
            vx = random.uniform(-15, 15)
            vy = random.uniform(-35, -10)
            col = random.choice([(255, 60, 20), (255, 160, 30), (255, 230, 80)])
            self.particles.append(Particle(x, y, vx, vy, col, lifetime=random.uniform(0.2, 0.35), size=2))

    def update(self, dt: float) -> None:
        """Обновляет все частицы и спецэффекты."""
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive]

        for s in self.shockwaves:
            s.update(dt)
        self.shockwaves = [s for s in self.shockwaves if s.is_alive]

        for w in self.whirlwinds:
            w.update(dt)
        self.whirlwinds = [w for w in self.whirlwinds if w.is_alive]

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовывает частицы и волны поверх поля."""
        for s in self.shockwaves:
            s.draw(surface)
        for w in self.whirlwinds:
            w.draw(surface)
        for p in self.particles:
            p.draw(surface)
