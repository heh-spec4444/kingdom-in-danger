"""
Модуль процедурной 8-bit аудиосистемы игры (Этап 6).
Включает:
- Встроенный математический синтезатор ретро-звуков (без внешних аудиофайлов):
  - выстрел стрелы (arrow)
  - удар мечом в ближнем бою (sword_hit)
  - умение [Q] «Вихрь клинков» (skill_q)
  - умение [W] «Боевой клич» (skill_w)
  - звон золотых монет (coin)
  - строительство и апгрейд башен (build)
  - фанфары нового уровня (level_up)
  - победный гимн (victory)
  - трагический аккорд поражения (defeat)
  - клик интерфейса (click)
- Управление звуком: включение/выключение звука (Mute), раздельная регулировка громкости
"""

import io
import math
import random
import struct
import wave
from typing import Dict, Optional, Callable
import pygame


class SoundManager:
    """Управляет процедурным синтезом, кэшированием и воспроизведением 8-bit звуков."""

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.is_muted = False
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self._initialized = False

        self._init_mixer_and_sounds()

    def _init_mixer_and_sounds(self) -> None:
        """Инициализирует аудиоподсистему pygame.mixer и генерирует звуковой банк."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
            self._synthesize_all()
            self._initialized = True
        except Exception as e:
            # Если аудиоустройство недоступно (например, в CI/сервере), работаем бесшумно
            print(f"[SoundManager] Предупреждение: аудиоподсистема недоступна ({e}). Звук отключён.")
            self._initialized = False
            self.is_muted = True

    def _make_sound(self, duration: float, synth_fn: Callable[[float, int, int], float]) -> Optional[pygame.mixer.Sound]:
        """Генерирует объект pygame.mixer.Sound из математической функции сэмплов."""
        try:
            total_samples = int(self.sample_rate * duration)
            raw_data = bytearray()
            for i in range(total_samples):
                t = i / self.sample_rate
                sample = synth_fn(t, i, total_samples)
                val = max(-1.0, min(1.0, sample))
                raw_data.extend(struct.pack("<h", int(val * 13500)))

            buf = io.BytesIO()
            with wave.open(buf, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(self.sample_rate)
                w.writeframes(raw_data)
            buf.seek(0)
            return pygame.mixer.Sound(buf)
        except Exception:
            return None

    def _synthesize_all(self) -> None:
        """Синтезирует весь звуковой банк 8-bit ретро-эффектов."""
        # 1. Клик интерфейса
        self.sounds["click"] = self._make_sound(
            0.04, lambda t, i, n: math.sin(2 * math.pi * 900 * t) * (1.0 - i / n)
        )

        # 2. Звон монет (+gold)
        self.sounds["coin"] = self._make_sound(
            0.18, lambda t, i, n: math.sin(2 * math.pi * (987 if t < 0.08 else 1318) * t) * (1.0 - (i / n) ** 0.5)
        )

        # 3. Выстрел стрелы (быстрый свист)
        self.sounds["arrow"] = self._make_sound(
            0.12,
            lambda t, i, n: (random.uniform(-0.5, 0.5) + 0.5 * math.sin(2 * math.pi * (1400 - 9000 * t) * t))
            * (1.0 - i / n),
        )

        # 4. Удар мечом (металлический рубящий лязг)
        self.sounds["sword_hit"] = self._make_sound(
            0.10,
            lambda t, i, n: (random.uniform(-0.6, 0.6) + 0.4 * math.sin(2 * math.pi * 360 * t))
            * (1.0 - i / n),
        )

        # 5. Магический астральный взрыв (Башня магов)
        self.sounds["magic_burst"] = self._make_sound(
            0.26,
            lambda t, i, n: math.sin(2 * math.pi * (520 + 160 * math.sin(38 * t)) * t) * (1.0 - i / n),
        )

        # 6. Навык [Q] «Вихрь клинков» (рассекающий воздух вихрь)
        self.sounds["skill_q"] = self._make_sound(
            0.32,
            lambda t, i, n: (random.uniform(-0.4, 0.4) + 0.6 * math.sin(2 * math.pi * (620 - 320 * t) * t))
            * (1.0 - i / n),
        )

        # 8. Навык [W] «Боевой клич» (звучный рог командира)
        self.sounds["skill_w"] = self._make_sound(
            0.40,
            lambda t, i, n: math.sin(2 * math.pi * (340 + 120 * math.sin(7 * t)) * t) * (1.0 - i / n),
        )

        # 9. Повышение уровня (радостный восходящий перелив C5-E5-G5)
        self.sounds["level_up"] = self._make_sound(
            0.36,
            lambda t, i, n: math.sin(
                2 * math.pi * (523 if t < 0.12 else (659 if t < 0.24 else 784)) * t
            ) * (1.0 - i / n),
        )

        # 10. Строительство и улучшение башни
        self.sounds["build"] = self._make_sound(
            0.14,
            lambda t, i, n: math.sin(2 * math.pi * (720 if t < 0.06 else 980) * t) * (1.0 - i / n),
        )

        # 11. Триумф Победы (королевские 8-bit фанфары)
        self.sounds["victory"] = self._make_sound(
            0.68,
            lambda t, i, n: math.sin(
                2 * math.pi * (523 if t < 0.15 else (659 if t < 0.30 else (784 if t < 0.45 else 1046))) * t
            ) * (1.0 - i / n),
        )

        # 12. Поражение (трагический нисходящий гул)
        self.sounds["defeat"] = self._make_sound(
            0.75,
            lambda t, i, n: (1.0 if math.sin(2 * math.pi * (390 - 290 * t) * t) > 0 else -1.0)
            * (1.0 - i / n),
        )

        # 13. Гибель командира
        self.sounds["hero_death"] = self._make_sound(
            0.38,
            lambda t, i, n: (random.uniform(-0.5, 0.5) + 0.5 * math.sin(2 * math.pi * (260 - 180 * t) * t))
            * (1.0 - i / n),
        )

    def play(self, sound_name: str, volume: float = 1.0) -> None:
        """Воспроизводит звук по имени, если звук включён."""
        if self.is_muted or not self._initialized:
            return
        snd = self.sounds.get(sound_name)
        if snd:
            try:
                snd.set_volume(max(0.0, min(1.0, volume)))
                snd.play()
            except Exception:
                pass

    def toggle_mute(self) -> bool:
        """Переключает режим звука (Вкл / Выкл). Возвращает текущее состояние is_muted."""
        self.is_muted = not self.is_muted
        if not self.is_muted and not self._initialized:
            self._init_mixer_and_sounds()
        return self.is_muted


# Глобальный синглтон менеджера звука
_sound_instance: Optional[SoundManager] = None


def get_sound_manager() -> SoundManager:
    """Возвращает глобальный экземпляр SoundManager."""
    global _sound_instance
    if _sound_instance is None:
        _sound_instance = SoundManager()
    return _sound_instance


def play_sound(sound_name: str, volume: float = 1.0) -> None:
    """Быстрый глобальный хелпер для вызова звука."""
    get_sound_manager().play(sound_name, volume)
