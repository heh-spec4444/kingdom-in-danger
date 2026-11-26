"""
Модуль финальных экранов Победы и Поражения (End Game Screen) — Этап 6.
Отображает:
- Величественную пергаментную панель с 3D-скосом и заклёпками в стиле Kingdom Rush
- Заголовок Победы / Поражения с сиянием
- Детальный расчёт очков по формуле баланса
- Таблицу Топ-5 рекордов Королевства с подсветкой текущего результата
- Интерактивную кнопку «ЗАНОВО» для мгновенного перезапуска игры
"""

from typing import Optional, Dict, Any, List
import pygame
from settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT
from core.assets import get_font
from core.sound import play_sound
from ui.high_scores import add_record, load_records, calculate_score


def _draw_beveled_box(
    surface: pygame.Surface,
    x: int,
    y: int,
    w: int,
    h: int,
    bg_color=(36, 26, 18),
    is_gold: bool = False,
    with_rivets: bool = True,
) -> None:
    """Рисует панель с 3D-скосом и заклёпками в стиле Kingdom Rush."""
    s_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    s_surf.fill((0, 0, 0, 170))
    surface.blit(s_surf, (x + 2, y + 3))

    plate_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, bg_color, plate_rect)

    outline_col = (18, 12, 8)
    pygame.draw.rect(surface, outline_col, plate_rect, 1)

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

    if with_rivets and w >= 20 and h >= 20:
        for rx, ry in [(x + 4, y + 4), (x + w - 6, y + 4), (x + 4, y + h - 6), (x + w - 6, y + h - 6)]:
            surface.set_at((rx, ry), (255, 245, 170))
            surface.set_at((rx + 1, ry), (210, 165, 55))
            surface.set_at((rx, ry + 1), (150, 105, 30))
            surface.set_at((rx + 1, ry + 1), (25, 16, 10))


class EndScreen:
    """Управляет показом экранов Победы и Поражения, рекордами и перезапуском."""

    def __init__(self):
        self.is_active = False
        self.outcome = "victory"  # "victory" или "defeat"
        self.width = 580
        self.height = 396
        self.x = (VIRTUAL_WIDTH - self.width) // 2
        self.y = (VIRTUAL_HEIGHT - self.height) // 2

        self.font_title = get_font(20)
        self.font_bold = get_font(15)
        self.font_main = get_font(13)
        self.font_small = get_font(12)

        self.btn_restart_rect = pygame.Rect(self.x + 70, self.y + self.height - 48, 200, 36)
        self.btn_menu_rect = pygame.Rect(self.x + 310, self.y + self.height - 48, 200, 36)
        self.btn_hovered = False
        self.btn_menu_hovered = False

        self.stats: Dict[str, Any] = {}
        self.top_records: List[Dict[str, Any]] = []
        self.current_rank: int = 0
        self.is_new_record: bool = False
        self._sound_played = False

    def show(
        self,
        outcome: str,
        hero_name: Optional[str] = None,
        castle_hp: int = 0,
        gold: int = 0,
        kills: int = 0,
        waves_cleared: int = 0,
    ) -> None:
        """Активирует финальный экран, рассчитывает очки и обновляет таблицу рекордов."""
        self.is_active = True
        self.outcome = outcome
        self._sound_played = False

        display_name = hero_name or "Оборона башнями"
        total_score, is_top_5, rank, record = add_record(
            display_name, castle_hp, gold, kills, waves_cleared
        )

        self.stats = {
            "hero_name": display_name,
            "castle_hp": castle_hp,
            "gold": gold,
            "kills": kills,
            "waves": waves_cleared,
            "score": total_score,
            "rank": rank,
            "is_top_5": is_top_5,
        }
        self.current_rank = rank
        self.is_new_record = is_top_5
        self.top_records = load_records()

        # Воспроизведение звукового триумфа или поражения
        if outcome == "victory":
            play_sound("victory", volume=1.0)
        else:
            play_sound("defeat", volume=1.0)

    def hide(self) -> None:
        self.is_active = False
        self._sound_played = False

    def update_hover(self, vx: int, vy: int) -> None:
        if self.is_active:
            self.btn_hovered = self.btn_restart_rect.collidepoint(vx, vy)
            self.btn_menu_hovered = self.btn_menu_rect.collidepoint(vx, vy)

    def handle_click(self, vx: int, vy: int) -> Optional[str]:
        """Обрабатывает клик по экрану. Возвращает 'restart', 'menu' или None."""
        if not self.is_active:
            return None

        if self.btn_restart_rect.collidepoint(vx, vy):
            play_sound("click", volume=1.0)
            self.hide()
            return "restart"

        if self.btn_menu_rect.collidepoint(vx, vy):
            play_sound("click", volume=1.0)
            self.hide()
            return "menu"

        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовывает финальный экран поверх игрового поля."""
        if not self.is_active:
            return

        x, y, w, h = self.x, self.y, self.width, self.height

        # Полупрозрачное затемнение поля
        dim_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 140))
        surface.blit(dim_surf, (0, 0))

        is_vic = (self.outcome == "victory")
        bg_color = (36, 28, 20) if is_vic else (36, 20, 20)

        _draw_beveled_box(surface, x, y, w, h, bg_color=bg_color, is_gold=is_vic, with_rivets=True)

        in_x, in_y, in_w, in_h = x + 10, y + 10, w - 20, h - 20
        in_bg = (44, 34, 25) if is_vic else (42, 26, 26)
        pygame.draw.rect(surface, in_bg, (in_x, in_y, in_w, in_h))
        pygame.draw.rect(surface, (20, 14, 10), (in_x, in_y, in_w, in_h), 1)

        # 1. Заголовок
        title_str = "ВЕЛИКАЯ ПОБЕДА!" if is_vic else "КОРОЛЕВСТВО ПАЛО"
        title_col = (255, 225, 75) if is_vic else (255, 75, 75)
        sub_str = "Все 10 волн отбиты, Королевство спасено!" if is_vic else "Цитадель разрушена натиском орды..."

        t_surf = self.font_title.render(title_str, True, title_col)
        sh_surf = self.font_title.render(title_str, True, (15, 10, 8))
        tx = x + (w - t_surf.get_width()) // 2
        surface.blit(sh_surf, (tx + 2, y + 18))
        surface.blit(t_surf, (tx, y + 16))

        sub_surf = self.font_small.render(sub_str, True, (215, 195, 170))
        surface.blit(sub_surf, (x + (w - sub_surf.get_width()) // 2, y + 48))

        pygame.draw.line(surface, (170, 130, 60), (x + 20, y + 72), (x + w - 20, y + 72), 1)

        # 2. Левая колонка: Детализация очков
        left_x = x + 20
        top_y = y + 76
        self._draw_text(surface, "РАСЧЁТ ОЧКОВ:", self.font_bold, left_x, top_y, (255, 220, 90))

        hp_pts = self.stats.get("castle_hp", 0) * 150
        gold_pts = self.stats.get("gold", 0) * 2
        kill_pts = self.stats.get("kills", 0) * 10
        wave_pts = self.stats.get("waves", 0) * 500
        total_pts = self.stats.get("score", 0)

        breakdown = [
            ("Замок (HP):", f"+{hp_pts}"),
            ("Казна (Gold):", f"+{gold_pts}"),
            ("Врагов убито:", f"+{kill_pts}"),
            ("Волн отбито:", f"+{wave_pts}"),
        ]

        sy = top_y + 28
        for lbl, val in breakdown:
            self._draw_text(surface, lbl, self.font_small, left_x, sy, (205, 195, 180))
            self._draw_text(surface, val, self.font_bold, left_x + 150, sy - 1, (240, 230, 210))
            sy += 24

        pygame.draw.line(surface, (120, 90, 45), (left_x, sy + 6), (left_x + 220, sy + 6), 1)
        self._draw_text(surface, "ИТОГО:", self.font_bold, left_x, sy + 14, (255, 235, 140))
        self._draw_text(surface, str(total_pts), self.font_bold, left_x + 150, sy + 14, (255, 225, 75))

        # 3. Правая колонка: Таблица ТОП-5 рекордов
        right_x = x + 270
        pygame.draw.line(surface, (120, 90, 45), (right_x - 14, top_y), (right_x - 14, y + h - 58), 1)

        self._draw_text(surface, "ТОП-5 РЕКОРДОВ:", self.font_bold, right_x, top_y, (255, 220, 90))

        self._draw_text(surface, "#", self.font_small, right_x, top_y + 28, (170, 155, 135))
        self._draw_text(surface, "Командир", self.font_small, right_x + 22, top_y + 28, (170, 155, 135))
        self._draw_text(surface, "Волн", self.font_small, right_x + 174, top_y + 28, (170, 155, 135))
        self._draw_text(surface, "Счёт", self.font_small, right_x + 224, top_y + 28, (170, 155, 135))

        ry = top_y + 50
        for idx, rec in enumerate(self.top_records[:5]):
            rank = idx + 1
            is_cur = (rank == self.current_rank and self.stats.get("is_top_5", False))

            row_col = (255, 235, 120) if is_cur else (225, 220, 210)
            if rank == 1:
                medal = "1."
                m_col = (255, 215, 50)
            elif rank == 2:
                medal = "2."
                m_col = (215, 220, 230)
            elif rank == 3:
                medal = "3."
                m_col = (205, 140, 75)
            else:
                medal = f"{rank}."
                m_col = (170, 160, 150)

            if is_cur:
                hi_rect = pygame.Rect(right_x - 6, ry - 2, 294, 20)
                pygame.draw.rect(surface, (65, 50, 30), hi_rect)
                pygame.draw.rect(surface, (180, 140, 60), hi_rect, 1)

            self._draw_text(surface, medal, self.font_bold, right_x, ry - 1, m_col)
            r_name = rec.get("name", "Герой")[:14]
            self._draw_text(surface, r_name, self.font_small, right_x + 22, ry + 1, row_col)
            self._draw_text(surface, str(rec.get("waves", 0)), self.font_small, right_x + 184, ry + 1, row_col)
            self._draw_text(surface, str(rec.get("score", 0)), self.font_bold, right_x + 224, ry - 1, row_col)

            ry += 25

        # 4. Интерактивные кнопки «ИГРАТЬ СНОВА» и «В ГЛАВНОЕ МЕНЮ»
        # Кнопка «ИГРАТЬ СНОВА»
        bx, by, bw, bh = (
            self.btn_restart_rect.x,
            self.btn_restart_rect.y,
            self.btn_restart_rect.w,
            self.btn_restart_rect.h,
        )
        btn_bg = (55, 125, 50) if self.btn_hovered else (42, 90, 38)
        _draw_beveled_box(surface, bx, by, bw, bh, bg_color=btn_bg, is_gold=True, with_rivets=False)
        btn_txt = self.font_bold.render("ИГРАТЬ СНОВА", True, (255, 255, 255))
        surface.blit(btn_txt, (bx + (bw - btn_txt.get_width()) // 2, by + (bh - btn_txt.get_height()) // 2))

        # Кнопка «В ГЛАВНОЕ МЕНЮ»
        mx, my, mw, mh = (
            self.btn_menu_rect.x,
            self.btn_menu_rect.y,
            self.btn_menu_rect.w,
            self.btn_menu_rect.h,
        )
        menu_bg = (105, 45, 38) if self.btn_menu_hovered else (75, 32, 28)
        _draw_beveled_box(surface, mx, my, mw, mh, bg_color=menu_bg, is_gold=False, with_rivets=False)
        menu_txt = self.font_bold.render("В ГЛАВНОЕ МЕНЮ", True, (255, 230, 200))
        surface.blit(menu_txt, (mx + (mw - menu_txt.get_width()) // 2, my + (mh - menu_txt.get_height()) // 2))

    def _draw_text(self, surface: pygame.Surface, text: str, font, x: int, y: int, color) -> None:
        """Отрисовывает текст с пиксельной тенью."""
        sh = font.render(text, True, (15, 10, 8))
        surface.blit(sh, (x + 1, y + 1))
        txt = font.render(text, True, color)
        surface.blit(txt, (x, y))
