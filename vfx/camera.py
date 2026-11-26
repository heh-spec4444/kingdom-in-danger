"""
Модуль камеры и тряски экрана (Screen Shake):
Использует систему травмы (trauma):
- Плавное затухание
- Нелинейная отдача (trauma^2)
- Смещение финального кадра при мощных способностях и уроне замку
"""

import random
from typing import Tuple


class CameraShake:
    """Управляет динамической тряской экрана при взрывах и мощных навыках."""

    def __init__(self, max_offset_px: float = 6.0, decay_speed: float = 2.4):
        self.max_offset = max_offset_px
        self.decay = decay_speed
        self.trauma = 0.0

    def add_trauma(self, amount: float) -> None:
        """Добавляет импульс тряски (от 0.0 до 1.0)."""
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt: float) -> None:
        """Плавно гасит тряску экрана со временем."""
        if self.trauma > 0.0:
            self.trauma = max(0.0, self.trauma - dt * self.decay)

    def get_offset(self) -> Tuple[int, int]:
        """Возвращает текущее смещение камеры в пикселях (dx, dy)."""
        if self.trauma <= 0.001:
            return 0, 0

        # Нелинейная квадратичная сила отдачи (trauma^2)
        shake = self.trauma * self.trauma
        dx = int(self.max_offset * shake * random.uniform(-1.0, 1.0))
        dy = int(self.max_offset * shake * random.uniform(-1.0, 1.0))
        return dx, dy
