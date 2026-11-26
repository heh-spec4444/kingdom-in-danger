"""
Модуль Главного меню игры «Королевство в опасности» (Этап 7).
Включает:
- Главное меню: «Играть», «Рекорды», «Управление», «Выход»
- Экран выбора одного из 3 командиров (Рыцарь, Пиромант, Следопыт) с превью спрайтов, статами и умениями
- Модальное окно рекордов (Топ-5 из records.json)
- Памятку по управлению (ПКМ, ЛКМ, Q, W, C, Space, P)
- Звуковые эффекты кликов и наведения
"""

import math
from typing import Dict, Any, Optional, List, Tuple
import pygame
from settings import (
    HEROES,
    DEFAULT_HERO_ID,
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
)
from core.assets import get_font, get_hud_icon, get_hero_portrait
from core.sound import play_sound
from ui.high_scores import load_records


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
    """Рисует 3D-панель с деревянной/пергаментной текстурой и металлическими заклёпками."""
    # Тень
    s_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    s_surf.fill((0, 0, 0, 160))
    surface.blit(s_surf, (x + 2, y + 3))

    # Фоновая плитка
    plate_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, bg_color, plate_rect)

    # Деревянная текстура
    grain_col = (min(255, bg_color[0] + 6), min(255, bg_color[1] + 5), min(255, bg_color[2] + 4))
    for gy in range(y + 4, y + h - 3, 6):
        pygame.draw.line(surface, grain_col, (x + 3, gy), (x + w - 4, gy), 1)

    # Контур
    pygame.draw.rect(surface, (18, 12, 8), plate_rect, 1)

    # 3D-скос
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

    # Заклёпки
    if with_rivets and w >= 20 and h >= 20:
        rivets = [
            (x + 4, y + 4),
            (x + w - 6, y + 4),
            (x + 4, y + h - 6),
            (x + w - 6, y + h - 6),
        ]
        for rx, ry in rivets:
            surface.set_at((rx, ry), (255, 245, 170))
            surface.set_at((rx + 1, ry), (210, 165, 55))
            surface.set_at((rx, ry + 1), (150, 105, 30))
            surface.set_at((rx + 1, ry + 1), (25, 16, 10))


class MainMenu:
    """Главное меню игры с выбором командира, таблицей рекордов и управлением."""

    STATE_MAIN = "main"
    STATE_HERO_SELECT = "hero_select"
    STATE_RECORDS = "records"
    STATE_CONTROLS = "controls"

    def __init__(self):
        self.state = self.STATE_MAIN
        self.selected_hero_id = DEFAULT_HERO_ID or "knight"
        self.pulse_timer = 0.0

        # Шрифты под 960x720 (масштаб x1.5 -> 1440x1080)
        self.font_super = get_font(30)
        self.font_title = get_font(23)
        self.font_bold = get_font(17)
        self.font_main = get_font(15)
        self.font_small = get_font(13)

        # Кнопки Главного меню (виртуальные координаты 960x720)
        btn_w, btn_h = 270, 48
        bx = (VIRTUAL_WIDTH - btn_w) // 2
        self.btn_play = pygame.Rect(bx, 250, btn_w, btn_h)
        self.btn_records = pygame.Rect(bx, 314, btn_w, btn_h)
        self.btn_controls = pygame.Rect(bx, 378, btn_w, btn_h)
        self.btn_quit = pygame.Rect(bx, 442, btn_w, btn_h)

        # Динамическая раскладка карточек командиров (центрированная карточка Рыцаря)
        self.hero_cards: Dict[str, pygame.Rect] = {}
        hero_ids = list(HEROES.keys())
        card_w = 400 if len(hero_ids) == 1 else 300
        card_h = 330
        gap = 24
        total_w = len(hero_ids) * card_w + max(0, len(hero_ids) - 1) * gap
        start_x = (VIRTUAL_WIDTH - total_w) // 2
        for idx, h_id in enumerate(hero_ids):
            self.hero_cards[h_id] = pygame.Rect(start_x + idx * (card_w + gap), 120, card_w, card_h)

        self.btn_hero_back = pygame.Rect(VIRTUAL_WIDTH // 2 - 244, 520, 220, 48)
        self.btn_start_game = pygame.Rect(VIRTUAL_WIDTH // 2 + 24, 520, 220, 48)

        # Кнопки экранов Рекордов и Управления
        self.btn_back_records = pygame.Rect((VIRTUAL_WIDTH - 220) // 2, 570, 220, 44)
        self.btn_back_controls = pygame.Rect((VIRTUAL_WIDTH - 220) // 2, 570, 220, 44)

        # Кнопка звука в правом верхнем углу
        self.btn_sound_rect = pygame.Rect(VIRTUAL_WIDTH - 52, 12, 40, 40)

    def _get_virtual_mouse(self) -> Tuple[int, int]:
        """Пересчитывает позицию мыши из физического окна в виртуальное пространство 960x720."""
        mouse_pos = pygame.mouse.get_pos()
        disp_surf = pygame.display.get_surface()
        dw, dh = (disp_surf.get_width(), disp_surf.get_height()) if disp_surf else (WINDOW_WIDTH, WINDOW_HEIGHT)
        vx = int(mouse_pos[0] * (VIRTUAL_WIDTH / max(1, dw)))
        vy = int(mouse_pos[1] * (VIRTUAL_HEIGHT / max(1, dh)))
        return vx, vy

    def update(self, dt: float) -> None:
        """Обновляет таймер анимации меню."""
        self.pulse_timer += dt * 4.0

    def handle_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]) -> Optional[Dict[str, Any]]:
        """
        Обрабатывает события мыши и клавиатуры в меню.
        Возвращает словарь действия, например:
        {"action": "start_game", "hero_id": "knight"} или {"action": "quit"}
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state in (self.STATE_HERO_SELECT, self.STATE_RECORDS, self.STATE_CONTROLS):
                    play_sound("click", 0.7)
                    self.state = self.STATE_MAIN
                    return None
                elif self.state == self.STATE_MAIN:
                    return {"action": "quit"}
            elif event.key == pygame.K_RETURN:
                if self.state == self.STATE_MAIN:
                    play_sound("click", 0.8)
                    self.state = self.STATE_HERO_SELECT
                    return None
                elif self.state == self.STATE_HERO_SELECT:
                    play_sound("victory", 0.9)
                    return {"action": "start_game", "hero_id": self.selected_hero_id}

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = mouse_pos

            # Проверка кнопки звука
            if self.btn_sound_rect.collidepoint(mx, my):
                return {"action": "toggle_sound"}

            if self.state == self.STATE_MAIN:
                if self.btn_play.collidepoint(mx, my):
                    play_sound("click", 0.8)
                    self.state = self.STATE_HERO_SELECT
                    return None
                elif self.btn_records.collidepoint(mx, my):
                    play_sound("click", 0.8)
                    self.state = self.STATE_RECORDS
                    return None
                elif self.btn_controls.collidepoint(mx, my):
                    play_sound("click", 0.8)
                    self.state = self.STATE_CONTROLS
                    return None
                elif self.btn_quit.collidepoint(mx, my):
                    play_sound("click", 0.7)
                    return {"action": "quit"}

            elif self.state == self.STATE_HERO_SELECT:
                for h_id, rect in self.hero_cards.items():
                    if rect.collidepoint(mx, my):
                        self.selected_hero_id = h_id
                        play_sound("click", 0.85)
                        return None

                if self.btn_start_game.collidepoint(mx, my):
                    play_sound("victory", 0.9)
                    return {"action": "start_game", "hero_id": self.selected_hero_id}
                elif self.btn_hero_back.collidepoint(mx, my):
                    play_sound("click", 0.7)
                    self.state = self.STATE_MAIN
                    return None

            elif self.state == self.STATE_RECORDS:
                if self.btn_back_records.collidepoint(mx, my):
                    play_sound("click", 0.7)
                    self.state = self.STATE_MAIN
                    return None

            elif self.state == self.STATE_CONTROLS:
                if self.btn_back_controls.collidepoint(mx, my):
                    play_sound("click", 0.7)
                    self.state = self.STATE_MAIN
                    return None

        return None

    def draw(self, surface: pygame.Surface, sound_muted: bool = False) -> None:
        """Отрисовывает интерфейс меню в зависимости от текущего состояния."""
        self._draw_background(surface)
        self._draw_sound_button(surface, sound_muted)

        if self.state == self.STATE_MAIN:
            self._draw_main_screen(surface)
        elif self.state == self.STATE_HERO_SELECT:
            self._draw_hero_select_screen(surface)
        elif self.state == self.STATE_RECORDS:
            self._draw_records_screen(surface)
        elif self.state == self.STATE_CONTROLS:
            self._draw_controls_screen(surface)

    def _draw_background(self, surface: pygame.Surface) -> None:
        """Отрисовывает тёмный фэнтезийный фон с мягкой виньеткой."""
        surface.fill((22, 18, 26))

        # Декоративные полосы
        for y in range(0, VIRTUAL_HEIGHT, 8):
            c_val = 24 if (y // 8) % 2 == 0 else 20
            pygame.draw.line(surface, (c_val, c_val - 3, c_val + 4), (0, y), (VIRTUAL_WIDTH, y), 8)

        # Виньетка по краям
        vignette = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (10, 8, 12, 140), (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        pygame.draw.rect(vignette, (5, 4, 8, 220), (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT), 12)
        surface.blit(vignette, (0, 0))

    def _draw_sound_button(self, surface: pygame.Surface, sound_muted: bool) -> None:
        """Отрисовывает кнопку звука в верхнем правом углу."""
        bx, by, bw, bh = self.btn_sound_rect.x, self.btn_sound_rect.y, self.btn_sound_rect.w, self.btn_sound_rect.h
        _draw_beveled_box(surface, bx, by, bw, bh, bg_color=(36, 26, 18), is_gold=not sound_muted, with_rivets=True)
        icon = pygame.transform.scale(get_hud_icon("sound"), (22, 22))
        surface.blit(icon, (bx + (bw - icon.get_width()) // 2, by + (bh - icon.get_height()) // 2))
        if sound_muted:
            pygame.draw.line(surface, (235, 45, 45), (bx + 7, by + 7), (bx + bw - 8, by + bh - 8), 2)

    def _draw_main_screen(self, surface: pygame.Surface) -> None:
        """Главный экран с величественным логотипом и кнопками навигации."""
        pulse = math.sin(self.pulse_timer) * 3.0
        ty = int(96 + pulse)

        sh = self.font_super.render("КОРОЛЕВСТВО В ОПАСНОСТИ", True, (15, 10, 8))
        surface.blit(sh, ((VIRTUAL_WIDTH - sh.get_width()) // 2 + 2, ty + 2))

        title = self.font_super.render("КОРОЛЕВСТВО В ОПАСНОСТИ", True, (255, 225, 75))
        surface.blit(title, ((VIRTUAL_WIDTH - title.get_width()) // 2, ty))

        sub = self.font_bold.render("TOWER DEFENSE + RTS HYBRID", True, (215, 185, 140))
        surface.blit(sub, ((VIRTUAL_WIDTH - sub.get_width()) // 2, ty + 50))

        cy = ty + 84
        cx = VIRTUAL_WIDTH // 2
        pygame.draw.line(surface, (220, 175, 60), (cx - 230, cy), (cx + 230, cy), 2)
        pygame.draw.circle(surface, (255, 235, 120), (cx, cy), 4)

        vx, vy = self._get_virtual_mouse()

        buttons = [
            (self.btn_play, "ИГРАТЬ", (55, 125, 50), True),
            (self.btn_records, "РЕКОРДЫ", (48, 38, 28), False),
            (self.btn_controls, "УПРАВЛЕНИЕ", (48, 38, 28), False),
            (self.btn_quit, "ВЫХОД", (75, 32, 28), False),
        ]

        for rect, label, bg, is_primary in buttons:
            is_hover = rect.collidepoint(vx, vy)
            b_col = (min(255, bg[0] + 25), min(255, bg[1] + 25), min(255, bg[2] + 25)) if is_hover else bg
            _draw_beveled_box(surface, rect.x, rect.y, rect.w, rect.h, bg_color=b_col, is_gold=is_hover or is_primary, with_rivets=True)

            txt_col = (255, 255, 255) if is_hover else ((255, 240, 160) if is_primary else (230, 220, 205))
            txt = self.font_bold.render(label, True, txt_col)
            surface.blit(txt, (rect.x + (rect.w - txt.get_width()) // 2, rect.y + (rect.h - txt.get_height()) // 2))

    def _draw_hero_select_screen(self, surface: pygame.Surface) -> None:
        """Экран выбора командира с карточкой Рыцаря-командира под 960x720."""
        h_txt = self.font_title.render("ВЫБЕРИТЕ КОМАНДИРА", True, (255, 225, 75))
        sh = self.font_title.render("ВЫБЕРИТЕ КОМАНДИРА", True, (15, 10, 8))
        surface.blit(sh, ((VIRTUAL_WIDTH - sh.get_width()) // 2 + 2, 48))
        surface.blit(h_txt, ((VIRTUAL_WIDTH - h_txt.get_width()) // 2, 46))

        vx, vy = self._get_virtual_mouse()

        for h_id, rect in self.hero_cards.items():
            is_sel = (self.selected_hero_id == h_id)
            is_hov = rect.collidepoint(vx, vy)
            h_data = HEROES[h_id]

            bg_col = (42, 34, 26) if is_sel else ((36, 28, 22) if is_hov else (28, 22, 18))
            _draw_beveled_box(surface, rect.x, rect.y, rect.w, rect.h, bg_color=bg_col, is_gold=is_sel, with_rivets=True)

            if is_sel:
                pulse_border = pygame.Surface((rect.w + 6, rect.h + 6), pygame.SRCALPHA)
                pygame.draw.rect(pulse_border, (255, 235, 90, 200), (0, 0, rect.w + 6, rect.h + 6), 2)
                surface.blit(pulse_border, (rect.x - 3, rect.y - 3))

            name_col = (255, 235, 110) if is_sel else (235, 225, 210)
            n_txt = self.font_bold.render(h_data["name"], True, name_col)
            surface.blit(n_txt, (rect.x + (rect.w - n_txt.get_width()) // 2, rect.y + 18))

            t_txt = self.font_small.render(h_data.get("title", ""), True, (200, 175, 135))
            surface.blit(t_txt, (rect.x + (rect.w - t_txt.get_width()) // 2, rect.y + 44))

            # Крупный бюст-портрет Рыцаря (без растягивания, 80x80 внутри рамки 96x96)
            pv_w, pv_h = 96, 96
            pv_x = rect.x + (rect.w - pv_w) // 2
            pv_y = rect.y + 72
            _draw_beveled_box(surface, pv_x, pv_y, pv_w, pv_h, bg_color=(24, 20, 28), is_gold=is_sel, with_rivets=False)

            portrait = get_hero_portrait(h_id)
            if portrait is not None:
                spr = pygame.transform.scale(portrait, (80, 80))
                surface.blit(spr, (pv_x + (pv_w - 80) // 2, pv_y + (pv_h - 80) // 2))

            stats_y = rect.y + 186
            pygame.draw.line(surface, (120, 90, 45), (rect.x + 20, stats_y - 4), (rect.x + rect.w - 20, stats_y - 4), 1)

            hp_txt = f"HP: {h_data['hp']}   |   Урон: {h_data['attack_damage']}"
            s1 = self.font_main.render(hp_txt, True, (255, 210, 140))
            surface.blit(s1, (rect.x + (rect.w - s1.get_width()) // 2, stats_y + 8))

            spd_txt = f"Скорость: {int(h_data['speed'])} px/s   |   КД: {h_data.get('attack_cooldown', 0.75)}с"
            s2 = self.font_small.render(spd_txt, True, (205, 195, 180))
            surface.blit(s2, (rect.x + (rect.w - s2.get_width()) // 2, stats_y + 34))

            rng_txt = f"Дальность ближнего боя: {int(h_data.get('attack_range', 36))} px"
            s3 = self.font_small.render(rng_txt, True, (160, 215, 245))
            surface.blit(s3, (rect.x + (rect.w - s3.get_width()) // 2, stats_y + 60))

            if is_sel:
                badge = self.font_bold.render("ВЫБРАН", True, (255, 240, 130))
                badge_bg = pygame.Rect(rect.x + (rect.w - 110) // 2, rect.y + rect.h - 36, 110, 26)
                pygame.draw.rect(surface, (65, 45, 20), badge_bg)
                pygame.draw.rect(surface, (255, 225, 75), badge_bg, 1)
                surface.blit(badge, (badge_bg.x + (badge_bg.w - badge.get_width()) // 2, badge_bg.y + 3))

        is_hov_back = self.btn_hero_back.collidepoint(vx, vy)
        _draw_beveled_box(surface, self.btn_hero_back.x, self.btn_hero_back.y, self.btn_hero_back.w, self.btn_hero_back.h, bg_color=(65, 32, 28) if is_hov_back else (48, 24, 20), is_gold=False, with_rivets=True)
        b_txt = self.font_bold.render("НАЗАД", True, (240, 225, 215))
        surface.blit(b_txt, (self.btn_hero_back.x + (self.btn_hero_back.w - b_txt.get_width()) // 2, self.btn_hero_back.y + (self.btn_hero_back.h - b_txt.get_height()) // 2))

        is_hov_start = self.btn_start_game.collidepoint(vx, vy)
        _draw_beveled_box(surface, self.btn_start_game.x, self.btn_start_game.y, self.btn_start_game.w, self.btn_start_game.h, bg_color=(55, 135, 50) if is_hov_start else (42, 100, 38), is_gold=True, with_rivets=True)
        s_txt = self.font_bold.render("В БОЙ!", True, (255, 255, 255))
        surface.blit(s_txt, (self.btn_start_game.x + (self.btn_start_game.w - s_txt.get_width()) // 2, self.btn_start_game.y + (self.btn_start_game.h - s_txt.get_height()) // 2))

    def _draw_records_screen(self, surface: pygame.Surface) -> None:
        """Экран лучших результатов (Топ-5 из records.json)."""
        pw, ph = 740, 420
        px = (VIRTUAL_WIDTH - pw) // 2
        py = 104
        _draw_beveled_box(surface, px, py, pw, ph, bg_color=(36, 26, 20), is_gold=True, with_rivets=True)

        h_txt = self.font_title.render("ТАБЛИЦА РЕКОРДОВ (ТОП-5)", True, (255, 225, 75))
        surface.blit(h_txt, (px + (pw - h_txt.get_width()) // 2, py + 22))

        col_y = py + 68
        pygame.draw.line(surface, (120, 90, 45), (px + 24, col_y + 26), (px + pw - 24, col_y + 26), 1)

        self._draw_text(surface, "#", self.font_bold, px + 28, col_y, (200, 175, 135))
        self._draw_text(surface, "Командир", self.font_bold, px + 72, col_y, (200, 175, 135))
        self._draw_text(surface, "Волны", self.font_bold, px + 320, col_y, (200, 175, 135))
        self._draw_text(surface, "Убито", self.font_bold, px + 425, col_y, (200, 175, 135))
        self._draw_text(surface, "Дата", self.font_bold, px + 525, col_y, (200, 175, 135))
        self._draw_text(surface, "Очки", self.font_bold, px + 635, col_y, (255, 225, 75))

        records = load_records()
        row_y = col_y + 42
        for i, rec in enumerate(records[:5]):
            rank = i + 1
            r_col = (255, 225, 75) if rank == 1 else ((215, 215, 225) if rank == 2 else ((205, 140, 75) if rank == 3 else (185, 180, 170)))

            self._draw_text(surface, str(rank), self.font_bold, px + 28, row_y, r_col)
            self._draw_text(surface, str(rec.get("name", "Герой"))[:16], self.font_main, px + 72, row_y + 1, (240, 235, 225))
            self._draw_text(surface, str(rec.get("waves", 0)), self.font_main, px + 340, row_y + 1, (220, 220, 220))
            self._draw_text(surface, str(rec.get("kills", 0)), self.font_main, px + 444, row_y + 1, (220, 220, 220))
            self._draw_text(surface, str(rec.get("date", ""))[-5:], self.font_small, px + 525, row_y + 2, (160, 155, 145))
            self._draw_text(surface, str(rec.get("score", 0)), self.font_bold, px + 635, row_y, r_col)

            row_y += 46

        vx, vy = self._get_virtual_mouse()
        is_hov = self.btn_back_records.collidepoint(vx, vy)

        _draw_beveled_box(surface, self.btn_back_records.x, self.btn_back_records.y, self.btn_back_records.w, self.btn_back_records.h, bg_color=(65, 32, 28) if is_hov else (48, 24, 20), is_gold=is_hov, with_rivets=True)
        b_txt = self.font_bold.render("НАЗАД", True, (255, 235, 210))
        surface.blit(b_txt, (self.btn_back_records.x + (self.btn_back_records.w - b_txt.get_width()) // 2, self.btn_back_records.y + (self.btn_back_records.h - b_txt.get_height()) // 2))

    def _draw_controls_screen(self, surface: pygame.Surface) -> None:
        """Экран справки по управлению и горячим клавишам."""
        pw, ph = 740, 400
        px = (VIRTUAL_WIDTH - pw) // 2
        py = 112
        _draw_beveled_box(surface, px, py, pw, ph, bg_color=(36, 26, 20), is_gold=True, with_rivets=True)

        h_txt = self.font_title.render("УПРАВЛЕНИЕ И ГОРЯЧИЕ КЛАВИШИ", True, (255, 225, 75))
        surface.blit(h_txt, (px + (pw - h_txt.get_width()) // 2, py + 22))

        controls_data = [
            ("ПКМ (Правая кнопка)", "Перемещение командира по сетке (поиск пути A*)"),
            ("ЛКМ (Левая кнопка)", "Постройка, апгрейд и продажа башен, клики меню"),
            ("[C] (Клавиша C)", "Карточка командира и базовые характеристики"),
            ("[Пробел] / [>>]", "Запуск следующей волны или скорость 2x"),
            ("[P] / [||]", "Пауза игры"),
        ]

        cy = py + 76
        for key_tag, desc in controls_data:
            k_s = self.font_bold.render(key_tag, True, (255, 235, 120))
            d_s = self.font_main.render(desc, True, (230, 225, 215))
            surface.blit(k_s, (px + 28, cy))
            surface.blit(d_s, (px + 258, cy + 2))
            cy += 54

        vx, vy = self._get_virtual_mouse()
        is_hov = self.btn_back_controls.collidepoint(vx, vy)

        _draw_beveled_box(surface, self.btn_back_controls.x, self.btn_back_controls.y, self.btn_back_controls.w, self.btn_back_controls.h, bg_color=(65, 32, 28) if is_hov else (48, 24, 20), is_gold=is_hov, with_rivets=True)
        b_txt = self.font_bold.render("НАЗАД", True, (255, 235, 210))
        surface.blit(b_txt, (self.btn_back_controls.x + (self.btn_back_controls.w - b_txt.get_width()) // 2, self.btn_back_controls.y + (self.btn_back_controls.h - b_txt.get_height()) // 2))

    def _draw_text(self, surface: pygame.Surface, text: str, font, x: int, y: int, color) -> None:
        """Отрисовывает текст с пиксельной тенью."""
        sh = font.render(text, True, (15, 10, 8))
        surface.blit(sh, (x + 1, y + 1))
        txt = font.render(text, True, color)
        surface.blit(txt, (x, y))
