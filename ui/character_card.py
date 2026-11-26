"""
Модуль интерактивной Карточки персонажа (Character Card) в стиле Kingdom Rush.
Открывается по клавише [C] или по клику на портрет [C] в нижнем интерфейсе (под 1280x720):
- Пергаментная карточка с золотой чеканкой, заклёпками и закрывающим крестиком [X]
- Портрет командира, имя, титул, текущий уровень и шкала опыта (XP)
- Базовые характеристики: Здоровье, Урон, Скорость атаки, Скорость бега, Дальность
"""

from typing import Tuple
import pygame
from settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT
from core.assets import get_font, get_hero_portrait


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
    """Рисует панель с 3D-скосом и заклёпками в стиле Kingdom Rush."""
    s_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    s_surf.fill((0, 0, 0, 160))
    surface.blit(s_surf, (x + 3, y + 4))

    plate_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, bg_color, plate_rect)

    grain_col = (bg_color[0] + 6, bg_color[1] + 5, bg_color[2] + 4)
    for gy in range(y + 6, y + h - 4, 8):
        pygame.draw.line(surface, grain_col, (x + 4, gy), (x + w - 5, gy), 1)

    pygame.draw.rect(surface, (18, 12, 8), plate_rect, 1)

    if is_gold:
        b_light = (255, 230, 115)
        b_mid = (220, 175, 60)
        b_dark = (120, 80, 25)
    else:
        b_light = (215, 180, 100)
        b_mid = (170, 130, 65)
        b_dark = (70, 48, 22)

    pygame.draw.line(surface, b_light, (x + 1, y + 1), (x + w - 2, y + 1), 1)
    pygame.draw.line(surface, b_light, (x + 1, y + 1), (x + 1, y + h - 2), 1)
    pygame.draw.line(surface, b_mid, (x + 2, y + 2), (x + w - 3, y + 2), 1)
    pygame.draw.line(surface, b_mid, (x + 2, y + 2), (x + 2, y + h - 3), 1)
    pygame.draw.line(surface, b_dark, (x + 1, y + h - 2), (x + w - 2, y + h - 2), 1)
    pygame.draw.line(surface, b_dark, (x + w - 2, y + 1), (x + w - 2, y + h - 2), 1)

    if with_rivets and w >= 24 and h >= 24:
        rivets = [
            (x + 5, y + 5),
            (x + w - 7, y + 5),
            (x + 5, y + h - 7),
            (x + w - 7, y + h - 7),
        ]
        for rx, ry in rivets:
            surface.set_at((rx, ry), (255, 245, 170))
            surface.set_at((rx + 1, ry), (210, 165, 55))
            surface.set_at((rx, ry + 1), (150, 105, 30))
            surface.set_at((rx + 1, ry + 1), (25, 16, 10))


class CharacterCard:
    """Управляет отображением карточки командира (портрет, XP, базовые статы)."""

    def __init__(self):
        self.is_open = False
        self.width = 440
        self.height = 238
        self.x = (VIRTUAL_WIDTH - self.width) // 2
        self.y = (VIRTUAL_HEIGHT - self.height) // 2

        self.font_title = get_font(17)
        self.font_bold = get_font(15)
        self.font_main = get_font(13)
        self.font_small = get_font(12)

        self.btn_close_rect = pygame.Rect(self.x + self.width - 32, self.y + 8, 22, 22)

    def toggle(self) -> None:
        self.is_open = not self.is_open

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def handle_click(
        self, vx: int, vy: int, hero=None, particle_sys=None, floating_texts=None
    ) -> bool:
        """Обрабатывает клики мыши по карточке персонажа."""
        if not self.is_open or hero is None:
            self.close()
            return False

        card_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if not card_rect.collidepoint(vx, vy):
            self.close()
            return True

        if self.btn_close_rect.collidepoint(vx, vy):
            self.close()
            return True

        return True

    def draw(self, surface: pygame.Surface, hero=None) -> None:
        """Отрисовывает карточку командира с портретом, уровнем, XP и базовыми характеристиками."""
        if not self.is_open or hero is None:
            return

        x, y, w, h = self.x, self.y, self.width, self.height

        dim_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 105))
        surface.blit(dim_surf, (0, 0))

        _draw_beveled_box(surface, x, y, w, h, bg_color=(38, 28, 20), is_gold=True, with_rivets=True)

        in_x, in_y, in_w, in_h = x + 9, y + 9, w - 18, h - 18
        pygame.draw.rect(surface, (48, 36, 26), (in_x, in_y, in_w, in_h))
        pygame.draw.rect(surface, (25, 18, 12), (in_x, in_y, in_w, in_h), 1)

        # 1. Заголовок и кнопка [X]
        t_surf = self.font_title.render(f"{hero.name} — Ур. {hero.level}", True, (255, 225, 75))
        sh = self.font_title.render(f"{hero.name} — Ур. {hero.level}", True, (20, 14, 10))
        surface.blit(sh, (x + 22, y + 14))
        surface.blit(t_surf, (x + 20, y + 12))

        bx, by, bw, bh = self.btn_close_rect.x, self.btn_close_rect.y, self.btn_close_rect.w, self.btn_close_rect.h
        _draw_beveled_box(surface, bx, by, bw, bh, bg_color=(55, 24, 20), is_gold=False, with_rivets=False)
        pygame.draw.line(surface, (255, 215, 160), (bx + 6, by + 6), (bx + bw - 7, by + bh - 7), 2)
        pygame.draw.line(surface, (255, 215, 160), (bx + bw - 7, by + 6), (bx + 6, by + bh - 7), 2)

        pygame.draw.line(surface, (175, 135, 60), (x + 16, y + 44), (x + w - 16, y + 44), 1)
        pygame.draw.line(surface, (25, 18, 12), (x + 16, y + 45), (x + w - 16, y + 45), 1)

        # 2. Портрет героя слева (увеличен 2x для чёткости на 720x540 -> 1440x1080)
        p_x, p_y, p_w, p_h = x + 18, y + 52, 74, 78
        _draw_beveled_box(surface, p_x, p_y, p_w, p_h, bg_color=(28, 22, 32), is_gold=True, with_rivets=False)
        portrait = get_hero_portrait(getattr(hero, "hero_id", "knight"))
        portrait_2x = pygame.transform.scale(portrait, (64, 64))
        surface.blit(portrait_2x, (p_x + (p_w - 64) // 2, p_y + (p_h - 64) // 2))

        # 3. Шкала опыта (XP) и титул
        xp_x, xp_y, xp_w, xp_h = x + 104, y + 58, 312, 18
        pygame.draw.rect(surface, (20, 15, 10), (xp_x - 1, xp_y - 1, xp_w + 2, xp_h + 2))
        pygame.draw.rect(surface, (35, 45, 60), (xp_x, xp_y, xp_w, xp_h))
        xp_ratio = min(1.0, max(0.0, hero.xp / max(1, hero.xp_to_next)))
        if xp_ratio > 0.0:
            fill_w = int(xp_w * xp_ratio)
            pygame.draw.rect(surface, (50, 165, 245), (xp_x, xp_y, fill_w, xp_h))
            pygame.draw.line(surface, (140, 215, 255), (xp_x, xp_y), (xp_x + fill_w - 1, xp_y), 1)

        xp_lbl = self.font_small.render(f"XP: {hero.xp}/{hero.xp_to_next}", True, (255, 255, 255))
        surface.blit(xp_lbl, (xp_x + (xp_w - xp_lbl.get_width()) // 2, xp_y + 1))

        title_txt = self.font_main.render(hero.title, True, (215, 185, 140))
        surface.blit(title_txt, (x + 104, y + 86))

        status_str = "В строю" if hero.is_alive else f"Возрождение через {int(hero.respawn_timer)}с"
        status_col = (120, 240, 140) if hero.is_alive else (255, 110, 110)
        status_txt = self.font_small.render(status_str, True, status_col)
        surface.blit(status_txt, (x + 104, y + 108))

        # Разделитель характеристик
        pygame.draw.line(surface, (120, 90, 45), (x + 16, y + 142), (x + w - 16, y + 142), 1)

        # 4. Базовые характеристики (2 колонки)
        stats_left = [
            ("Здоровье:", f"{int(hero.hp)}/{hero.max_hp}", (255, 100, 100)),
            ("Урон атаки:", f"{hero.effective_damage}", (255, 205, 80)),
            ("Скорость атаки:", f"{hero.attack_cooldown:.2f}с", (230, 230, 230)),
        ]
        stats_right = [
            ("Скорость бега:", f"{int(hero.current_speed)} px/s", (255, 240, 160)),
            ("Дальность:", f"{int(hero.attack_range)} px", (140, 210, 255)),
        ]

        sy = y + 154
        for label, val, val_col in stats_left:
            lbl_s = self.font_small.render(label, True, (200, 190, 175))
            val_s = self.font_bold.render(val, True, val_col)
            surface.blit(lbl_s, (x + 20, sy))
            surface.blit(val_s, (x + 136, sy - 1))
            sy += 24

        sy = y + 154
        for label, val, val_col in stats_right:
            lbl_s = self.font_small.render(label, True, (200, 190, 175))
            val_s = self.font_bold.render(val, True, val_col)
            surface.blit(lbl_s, (x + 232, sy))
            surface.blit(val_s, (x + 344, sy - 1))
            sy += 24
