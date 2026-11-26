"""
Модуль плавающего интерфейса (Floating HUD) в эстетике Kingdom Rush.
Интерфейс не перекрывает карту сплошными полосами, а парит компактными виджетами поверх игрового поля:
- Сверху слева: 3D-плашка ресурсов с золотыми скосами (beveled edges), металлическими заклёпками и рельефными иконками
- Сверху справа: кнопка звука в бронзовой оправе с заклёпками
- Снизу слева: кнопки паузы (||) и ускорения волны (>>) с 3D-скосами
- Снизу по центру: 2 крупных медальона умений [Q] и [W] с золотой чеканкой и заклёпками
"""

from typing import Tuple, Optional
import pygame
from settings import (
    STARTING_GOLD,
    CASTLE_MAX_HP,
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
)
from core.assets import get_font, get_hud_icon


def _draw_beveled_box(
    surface: pygame.Surface,
    x: int,
    y: int,
    w: int,
    h: int,
    bg_color: Tuple[int, int, int] = (36, 26, 18),
    is_gold: bool = False,
    with_rivets: bool = True,
) -> None:
    """
    Рисует панель с выразительным 3D-скосом (beveled edges) и металлическими заклёпками:
    - Мягкая падающая тень
    - Тёмный внешний контур
    - Яркий верхне-левый световой блик и тёмно-бронзовый нижне-правый срез
    - Объёмные шляпки заклёпок по 4 углам
    """
    # 1. Тень
    s_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    s_surf.fill((0, 0, 0, 130))
    surface.blit(s_surf, (x + 1, y + 2))

    # 2. Фон панели (тёмный дуб или оружейный металл)
    plate_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, bg_color, plate_rect)

    # Текстурные полосы дерева / металла
    grain_col = (bg_color[0] + 8, bg_color[1] + 6, bg_color[2] + 4)
    for gy in range(y + 4, y + h - 3, 5):
        pygame.draw.line(surface, grain_col, (x + 3, gy), (x + w - 4, gy), 1)

    # 3. Внешний контур
    outline_col = (20, 14, 10)
    pygame.draw.rect(surface, outline_col, plate_rect, 1)

    # 4. 3D Beveled скос (свет сверху/слева, тень снизу/справа)
    if is_gold:
        bevel_light = (255, 228, 110)
        bevel_mid = (220, 175, 60)
        bevel_dark = (125, 85, 25)
    else:
        bevel_light = (215, 175, 90)
        bevel_mid = (175, 135, 65)
        bevel_dark = (75, 50, 22)

    # Верхний и левый блик
    pygame.draw.line(surface, bevel_light, (x + 1, y + 1), (x + w - 2, y + 1), 1)
    pygame.draw.line(surface, bevel_light, (x + 1, y + 1), (x + 1, y + h - 2), 1)
    pygame.draw.line(surface, bevel_mid, (x + 2, y + 2), (x + w - 3, y + 2), 1)
    pygame.draw.line(surface, bevel_mid, (x + 2, y + 2), (x + 2, y + h - 3), 1)

    # Нижняя и правая тень скоса
    pygame.draw.line(surface, bevel_dark, (x + 1, y + h - 2), (x + w - 2, y + h - 2), 1)
    pygame.draw.line(surface, bevel_dark, (x + w - 2, y + 1), (x + w - 2, y + h - 2), 1)

    # 5. Металлические заклёпки по 4 углам
    if with_rivets and w >= 20 and h >= 20:
        rivets = [
            (x + 3, y + 3),
            (x + w - 5, y + 3),
            (x + 3, y + h - 5),
            (x + w - 5, y + h - 5),
        ]
        for rx, ry in rivets:
            surface.set_at((rx, ry), (255, 248, 175))       # блик
            surface.set_at((rx + 1, ry), (210, 165, 55))   # тело заклепки
            surface.set_at((rx, ry + 1), (160, 115, 35))   # полутень
            surface.set_at((rx + 1, ry + 1), (28, 18, 12)) # тень


# Прямоугольники кликабельных кнопок интерфейса в виртуальных координатах 960x720
RECT_PAUSE_BTN = pygame.Rect(12, VIRTUAL_HEIGHT - 48, 36, 36)
RECT_WAVE_BTN = pygame.Rect(54, VIRTUAL_HEIGHT - 48, 44, 36)
RECT_SOUND_BTN = pygame.Rect(VIRTUAL_WIDTH - 48, 10, 36, 36)
RECT_HERO_CARD = pygame.Rect((VIRTUAL_WIDTH - 46) // 2, VIRTUAL_HEIGHT - 54, 46, 46)
RECT_PAUSE_RESUME = pygame.Rect((VIRTUAL_WIDTH - 210) // 2, (VIRTUAL_HEIGHT // 2) - 18, 210, 36)
RECT_PAUSE_MENU = pygame.Rect((VIRTUAL_WIDTH - 210) // 2, (VIRTUAL_HEIGHT // 2) + 28, 210, 36)


class HUD:
    """Управляет отрисовкой плавающего кинематографичного HUD поверх карты 960x720 (x1.5 -> 1440x1080)."""

    def __init__(self):
        self.font_small = get_font(12)
        self.font_mid = get_font(15)
        self.font_bold = get_font(16)

        # Прямоугольники для проверки кликов
        self.btn_pause_rect = RECT_PAUSE_BTN
        self.btn_wave_rect = RECT_WAVE_BTN
        self.btn_sound_rect = RECT_SOUND_BTN
        self.btn_hero_card_rect = RECT_HERO_CARD
        self.btn_pause_resume_rect = RECT_PAUSE_RESUME
        self.btn_pause_menu_rect = RECT_PAUSE_MENU

    def draw(
        self,
        surface: pygame.Surface,
        castle_hp: int = CASTLE_MAX_HP,
        gold: int = STARTING_GOLD,
        wave_num: int = 0,
        total_waves: int = 10,
        is_paused: bool = False,
        is_fast: bool = False,
        can_start_wave: bool = False,
        hero=None,
        sound_muted: bool = False,
    ) -> None:
        """Отрисовывает плавающие минималистичные виджеты поверх карты."""
        self._draw_resource_plaque(surface, castle_hp, gold, wave_num, total_waves)
        self._draw_top_controls(surface, sound_muted=sound_muted)
        self._draw_bottom_left_controls(surface, is_paused, is_fast, can_start_wave)
        self._draw_skill_medallions(surface, hero)

        # Оповещение о режиме паузы
        if is_paused:
            self._draw_pause_indicator(surface)

    def _draw_text_with_shadow(
        self, surface: pygame.Surface, text: str, font: pygame.font.Font, x: int, y: int, color: Tuple[int, int, int]
    ) -> None:
        """Рисует текст с чёткой пиксельной тенью для высокой читаемости."""
        shadow = font.render(text, True, (15, 10, 8))
        surface.blit(shadow, (x + 1, y + 1))
        txt = font.render(text, True, color)
        surface.blit(txt, (x, y))

    def _draw_resource_plaque(
        self, surface: pygame.Surface, castle_hp: int, gold: int, wave_num: int, total_waves: int
    ) -> None:
        """Сверху слева: 3D-плашка ресурсов под экран 960x720."""
        x, y, w, h = 12, 10, 268, 38

        _draw_beveled_box(surface, x, y, w, h, bg_color=(36, 26, 18), is_gold=False, with_rivets=True)

        # 1. Замок (HP)
        h_icon = pygame.transform.scale(get_hud_icon("heart_3d"), (20, 20))
        surface.blit(h_icon, (x + 10, y + 9))
        hp_color = (255, 100, 100) if castle_hp <= 5 else (250, 235, 235)
        self._draw_text_with_shadow(surface, str(castle_hp), self.font_bold, x + 34, y + 10, hp_color)

        pygame.draw.line(surface, (22, 16, 12), (x + 76, y + 6), (x + 76, y + h - 7), 2)
        pygame.draw.line(surface, (120, 85, 42), (x + 78, y + 6), (x + 78, y + h - 7), 1)

        # 2. Золото (Gold)
        c_icon = pygame.transform.scale(get_hud_icon("coin_3d"), (20, 20))
        surface.blit(c_icon, (x + 88, y + 9))
        self._draw_text_with_shadow(surface, str(gold), self.font_bold, x + 114, y + 10, (255, 225, 75))

        pygame.draw.line(surface, (22, 16, 12), (x + 172, y + 6), (x + 172, y + h - 7), 2)
        pygame.draw.line(surface, (120, 85, 42), (x + 174, y + 6), (x + 174, y + h - 7), 1)

        # 3. Волна (0/10)
        sk_icon = pygame.transform.scale(get_hud_icon("skull_3d"), (18, 18))
        surface.blit(sk_icon, (x + 184, y + 10))
        wave_str = f"{wave_num}/{total_waves}"
        self._draw_text_with_shadow(surface, wave_str, self.font_bold, x + 208, y + 10, (235, 230, 220))

    def _draw_top_controls(self, surface: pygame.Surface, sound_muted: bool = False) -> None:
        """Сверху справа: кнопка звука в 3D-оправе с индикацией Mute."""
        bx, by, bw, bh = self.btn_sound_rect.x, self.btn_sound_rect.y, self.btn_sound_rect.w, self.btn_sound_rect.h
        self._draw_square_btn(surface, bx, by, bw, bh, "sound", is_gold=not sound_muted)
        if sound_muted:
            pygame.draw.line(surface, (235, 45, 45), (bx + 8, by + 8), (bx + bw - 9, by + bh - 9), 3)

    def _draw_bottom_left_controls(
        self, surface: pygame.Surface, is_paused: bool, is_fast: bool, can_start_wave: bool
    ) -> None:
        """Снизу слева: кнопки паузы (||) и старта/ускорения волны (>>)."""
        p_bg = (62, 38, 22) if is_paused else (36, 26, 18)
        self._draw_square_btn(
            surface, self.btn_pause_rect.x, self.btn_pause_rect.y, self.btn_pause_rect.w, self.btn_pause_rect.h,
            "pause", is_gold=is_paused, custom_bg=p_bg
        )

        w_x, w_y, w_w, w_h = self.btn_wave_rect.x, self.btn_wave_rect.y, self.btn_wave_rect.w, self.btn_wave_rect.h
        w_bg = (68, 48, 25) if (is_fast or can_start_wave) else (42, 30, 20)
        _draw_beveled_box(surface, w_x, w_y, w_w, w_h, bg_color=w_bg, is_gold=True, with_rivets=True)
        w_icon = get_hud_icon("fast_forward")
        if is_fast:
            sc_ic = pygame.transform.scale(w_icon, (20, 20))
            surface.blit(sc_ic, (w_x + 5, w_y + (w_h - 20) // 2))
            t_2x = self.font_small.render("2x", True, (255, 240, 140))
            surface.blit(t_2x, (w_x + 25, w_y + 11))
        else:
            surface.blit(w_icon, (w_x + (w_w - w_icon.get_width()) // 2, w_y + (w_h - w_icon.get_height()) // 2))

    def _draw_pause_indicator(self, surface: pygame.Surface) -> None:
        """Отрисовывает меню паузы по центру экрана."""
        pw, ph = 264, 168
        px = (surface.get_width() - pw) // 2
        py = (surface.get_height() - ph) // 2

        veil = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 115))
        surface.blit(veil, (0, 0))

        _draw_beveled_box(surface, px, py, pw, ph, bg_color=(28, 20, 16), is_gold=True, with_rivets=True)

        p_txt = self.font_bold.render("ПАУЗА", True, (255, 235, 160))
        surface.blit(p_txt, (px + (pw - p_txt.get_width()) // 2, py + 16))

        rx, ry, rw, rh = self.btn_pause_resume_rect.x, self.btn_pause_resume_rect.y, self.btn_pause_resume_rect.w, self.btn_pause_resume_rect.h
        _draw_beveled_box(surface, rx, ry, rw, rh, bg_color=(45, 34, 22), is_gold=False, with_rivets=False)
        r_txt = self.font_small.render("ПРОДОЛЖИТЬ [P]", True, (255, 240, 180))
        surface.blit(r_txt, (rx + (rw - r_txt.get_width()) // 2, ry + (rh - r_txt.get_height()) // 2))

        mx, my, mw, mh = self.btn_pause_menu_rect.x, self.btn_pause_menu_rect.y, self.btn_pause_menu_rect.w, self.btn_pause_menu_rect.h
        _draw_beveled_box(surface, mx, my, mw, mh, bg_color=(55, 24, 20), is_gold=False, with_rivets=False)
        m_txt = self.font_small.render("В ГЛАВНОЕ МЕНЮ", True, (255, 210, 180))
        surface.blit(m_txt, (mx + (mw - m_txt.get_width()) // 2, my + (mh - m_txt.get_height()) // 2))

    def _draw_skill_medallions(self, surface: pygame.Surface, hero=None) -> None:
        """Снизу по центру: медальон портрета командира [C] (скрыт, если hero is None)."""
        if hero is None:
            return

        import math

        card_icon = getattr(hero, "icon_card", "knight_card_3d")

        cx, cy, cw, ch = (
            self.btn_hero_card_rect.x,
            self.btn_hero_card_rect.y,
            self.btn_hero_card_rect.w,
            self.btn_hero_card_rect.h,
        )
        self._draw_skill_box(surface, cx, cy, cw, ch, card_icon, "C")

        lvl_txt = self.font_small.render(f"v{hero.level}", True, (255, 235, 140))
        surface.blit(lvl_txt, (cx + cw - lvl_txt.get_width() - 5, cy + ch - 18))

        if not hero.is_alive:
            dim_c = pygame.Surface((cw, ch), pygame.SRCALPHA)
            dim_c.fill((60, 15, 15, 185))
            surface.blit(dim_c, (cx, cy))
            secs = int(math.ceil(hero.respawn_timer))
            s_txt = self.font_bold.render(f"{secs}s", True, (255, 90, 90))
            surface.blit(s_txt, (cx + (cw - s_txt.get_width()) // 2, cy + (ch - s_txt.get_height()) // 2))

    def _draw_square_btn(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        w: int,
        h: int,
        icon_name: str,
        is_gold: bool = False,
        custom_bg: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        """Отрисовывает компактную 3D-кнопку с заклёпками."""
        if custom_bg is not None:
            bg_col = custom_bg
        else:
            bg_col = (55, 38, 22) if is_gold else (36, 26, 18)
        _draw_beveled_box(surface, x, y, w, h, bg_color=bg_col, is_gold=is_gold, with_rivets=True)

        icon = get_hud_icon(icon_name)
        ix = x + (w - icon.get_width()) // 2
        iy = y + (h - icon.get_height()) // 2
        surface.blit(icon, (ix, iy))

    def _draw_skill_box(
        self, surface: pygame.Surface, x: int, y: int, w: int, h: int, icon_name: str, key_letter: str
    ) -> None:
        """Отрисовывает выразительный медальон способности [Q] или [W] с 3D-скосом и заклёпками."""
        # Основа с золотым 3D-скосом
        _draw_beveled_box(surface, x, y, w, h, bg_color=(28, 20, 32), is_gold=True, with_rivets=True)

        # 4. Иконка-медальон: если она шире кнопки, аккуратно ужимаем под 46x46
        icon = get_hud_icon(icon_name)
        max_ic = max(16, w - 10)
        if icon.get_width() > max_ic or icon.get_height() > max_ic:
            icon = pygame.transform.scale(icon, (max_ic, max_ic))
        ix = x + (w - icon.get_width()) // 2
        iy = y + (h - icon.get_height()) // 2
        surface.blit(icon, (ix, iy))

        # Микро-табличка с горячей клавишей [C] в углу
        tag_w, tag_h = 16, 15
        tag_x, tag_y = x + 4, y + 4
        pygame.draw.rect(surface, (20, 14, 10), (tag_x - 1, tag_y - 1, tag_w + 2, tag_h + 2))
        pygame.draw.rect(surface, (60, 42, 22), (tag_x, tag_y, tag_w, tag_h))
        pygame.draw.line(surface, (245, 215, 95), (tag_x, tag_y), (tag_x + tag_w - 1, tag_y), 1)

        k_txt = self.font_small.render(key_letter, True, (255, 240, 140))
        surface.blit(k_txt, (tag_x + (tag_w - k_txt.get_width()) // 2, tag_y - 1))

