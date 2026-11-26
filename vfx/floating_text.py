"""
Модуль всплывающего пиксельного текста (Floating Text):
- Цифры урона (-22) и критических ударов (-45)
- Начисление золота (+10g) и опыта (+15xp)
- Статусные эффекты («СТАН!», «LEVEL UP!», «БАФФ!»)
"""

from typing import List, Tuple
import pygame
from core.assets import get_font


class FloatingText:
    """Всплывающая текстовая надпись."""

    def __init__(
        self,
        text: str,
        x: float,
        y: float,
        color: Tuple[int, int, int],
        duration: float = 0.8,
        font_size: int = 14,
        vy: float = -36.0,
    ):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.duration = duration
        self.timer = 0.0
        self.vy = vy
        self.font = get_font(font_size)
        self.is_alive = True

    def update(self, dt: float) -> None:
        self.timer += dt
        if self.timer >= self.duration:
            self.is_alive = False
            return

        self.y += self.vy * dt
        # Замедление подъёма текста
        self.vy *= 0.94

    def draw(self, surface: pygame.Surface) -> None:
        if not self.is_alive:
            return

        # Тень текста
        sh = self.font.render(self.text, True, (15, 10, 8))
        txt = self.font.render(self.text, True, self.color)

        ix, iy = int(self.x - txt.get_width() // 2), int(self.y)
        surface.blit(sh, (ix + 1, iy + 1))
        surface.blit(txt, (ix, iy))


class FloatingTextManager:
    """Централизованный менеджер всех всплывающих надписей."""

    def __init__(self):
        self.texts: List[FloatingText] = []

    def clear(self) -> None:
        self.texts.clear()

    def add_damage(self, x: float, y: float, amount: int, is_critical: bool = False) -> None:
        """Всплывающий урон (красный или золотой для критов)."""
        col = (255, 185, 45) if is_critical else (255, 80, 80)
        prefix = "!" if is_critical else ""
        txt = f"{prefix}-{amount}"
        f_size = 17 if is_critical else 14
        self.texts.append(FloatingText(txt, x, y - 12, col, duration=0.75, font_size=f_size))

    def add_gold(self, x: float, y: float, amount: int) -> None:
        """Всплывающее золото (+10g)."""
        self.texts.append(FloatingText(f"+{amount}g", x, y - 14, (255, 215, 50), duration=0.85, font_size=14))

    def add_xp(self, x: float, y: float, amount: int) -> None:
        """Всплывающий опыт (+15xp)."""
        self.texts.append(FloatingText(f"+{amount}xp", x, y - 22, (90, 195, 255), duration=0.85, font_size=13))

    def add_status(self, x: float, y: float, text: str, color: Tuple[int, int, int] = (255, 230, 80)) -> None:
        """Статусный эффект (СТАН!, БАФФ!, РЕГЕН!)."""
        self.texts.append(FloatingText(text, x, y - 20, color, duration=0.9, font_size=15, vy=-30.0))

    def update(self, dt: float) -> None:
        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.is_alive]

    def draw(self, surface: pygame.Surface) -> None:
        for t in self.texts:
            t.draw(surface)
