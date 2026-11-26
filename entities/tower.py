"""
Модуль оборонительных башен (Башня лучников и Башня магов, уровни 1-7):
- PNG-анимации постройки/апгрейда (1 Upgrade/) и покоя (2 Idle/)
- Юниты на вершине башен (3 Units/1..3/) с U/D/S и отражением влево/вправо
- Отрисовка радиуса атаки при наведении и выборе
- Всплывающее меню постройки (Лучники + Маги), улучшения и продажи (возврат 70%)
"""

import math
from typing import List, Tuple, Dict, Optional, Callable
import pygame
from settings import (
    TOWERS,
    TOWER_SELL_RATIO,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    TILE_SIZE,
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
)
from entities.enemy import Enemy
from entities.projectile import Projectile
from core.assets import (
    ARCHER_TOWER_W,
    ARCHER_TOWER_H,
    ARCHER_UNIT_SIZE,
    get_tower_idle_frames,
    get_tower_upgrade_frames,
    get_tower_unit_frames,
    get_font,
)
from core.sound import play_sound

# Единая таблица якорей юнитов и геометрии спрайта 70x130 для каждого типа башен
_TOWER_VISUAL_CFG: Dict[str, Dict] = {
    "archer": {
        "anchors": {
            1: [(35, 90, 93)],
            2: [(35, 84, 86)],
            3: [(35, 74, 76)],
            4: [(35, 79, 73)],
            5: [(29, 68, 69), (43, 68, 69)],
            6: [(29, 67, 68), (43, 67, 68)],
            7: [(29, 80, 74), (43, 80, 74)],
        },
        "unit_tier": {1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 3, 7: 3},
        "top_y": {1: 62, 2: 56, 3: 46, 4: 33, 5: 35, 6: 34, 7: 16},
        "sound": "arrow",
        "menu_icon": ("archer", 1, (4, 42, 38, 42)),
    },
    "mage": {
        "anchors": {
            1: [(35, 91, 100)],
            2: [(35, 90, 100)],
            3: [(35, 88, 98)],
            4: [(27, 73, 75)],
            5: [(26, 65, 69), (44, 65, 69)],
            6: [(26, 61, 64), (44, 61, 64)],
            7: [],  # Закрытая конусная крыша: заряд срывается с верхнего кристалла
        },
        "unit_tier": {1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 3, 7: 3},
        "top_y": {1: 66, 2: 64, 3: 62, 4: 39, 5: 29, 6: 21, 7: 3},
        "sound": "magic_burst",
        "menu_icon": ("mage", 4, (4, 24, 38, 56)),
    },
}

MAX_ARCHER_TOWER_LEVEL = max(TOWERS["archer"]["levels"].keys())


class Tower:
    """Оборонительная башня (лучников или магов, уровни 1-7) на строительной площадке."""

    UPGRADE_ANIM_DURATION = 0.45
    ATTACK_ANIM_DURATION = 0.36
    PREATTACK_WINDOW = 0.18

    def __init__(self, tower_type: str = "archer", grid_pos: Tuple[int, int] = (0, 0)):
        self.tower_type = "archer" if tower_type not in TOWERS else tower_type
        self.grid_pos = grid_pos
        self.col, self.row = grid_pos

        self.x = float(MAP_OFFSET_X + self.col * TILE_SIZE + TILE_SIZE // 2)
        self.y = float(MAP_OFFSET_Y + self.row * TILE_SIZE + TILE_SIZE // 2)

        self.level = 1
        self.attack_timer = 0.0
        self.is_hovered = False
        self.is_selected = False

        self.idle_timer = (self.col * 0.17 + self.row * 0.23) % 2.0
        self.upgrade_anim_timer = self.UPGRADE_ANIM_DURATION
        self.attack_anim_timer = 0.0
        self.aim_dx = -1.0
        self.aim_dy = 1.0
        self.has_target = False
        self._active_unit_idx = 0

        cfg = TOWERS[self.tower_type]
        self.name = cfg["name"]
        self.color = cfg["color"]
        self.projectile_type = cfg["projectile_type"]
        self.total_invested = cfg["levels"][1]["cost"]
        self.max_level = max(cfg["levels"].keys())

        self._refresh_stats()

    def _refresh_stats(self) -> None:
        """Обновляет боевые характеристики при постройке или апгрейде."""
        lvl_cfg = TOWERS[self.tower_type]["levels"][self.level]
        self.attack_range = float(lvl_cfg["range"])
        self.damage = int(lvl_cfg["damage"])
        self.cooldown = float(lvl_cfg["cooldown"])
        self.level_name = lvl_cfg["name"]

        self.splash_radius = float(lvl_cfg.get("splash_radius", 0.0))
        self.slow_ratio = float(lvl_cfg.get("slow_ratio", 0.0))
        self.slow_duration = float(lvl_cfg.get("slow_duration", 0.0))
        self.ignore_armor = bool(lvl_cfg.get("ignore_armor", False))

    @property
    def can_upgrade(self) -> bool:
        return self.level < self.max_level

    @property
    def upgrade_cost(self) -> int:
        if not self.can_upgrade:
            return 0
        return TOWERS[self.tower_type]["levels"][self.level + 1]["cost"]

    @property
    def sell_refund(self) -> int:
        return max(1, int(self.total_invested * TOWER_SELL_RATIO))

    def upgrade(self) -> bool:
        """Повышает уровень башни до следующего и запускает анимацию апгрейда."""
        if not self.can_upgrade:
            return False
        next_cost = self.upgrade_cost
        self.level += 1
        self.total_invested += next_cost
        self.upgrade_anim_timer = self.UPGRADE_ANIM_DURATION
        self._refresh_stats()
        play_sound("build", 0.8)
        return True

    def _get_tower_top_left(self) -> Tuple[int, int]:
        """Возвращает левый верхний угол спрайта башни (основание совмещено с PlaceForTower1)."""
        draw_x = int(self.x - ARCHER_TOWER_W // 2)
        draw_y = int(self.y + 15 - ARCHER_TOWER_H)
        return draw_x, draw_y

    def _get_projectile_spawn_pos(self, anchors: List[Tuple[int, int, int]]) -> Tuple[float, float]:
        """Возвращает точку вылета снаряда (от активного юнита или кристалла на шпиле)."""
        draw_x, draw_y = self._get_tower_top_left()
        if not anchors:
            return self.x, draw_y + round(14 * ARCHER_TOWER_H / 130.0)
        cx, fy, _ = anchors[self._active_unit_idx % len(anchors)]
        wx = draw_x + cx * ARCHER_TOWER_W / 70.0
        wy = draw_y + (fy - 14) * ARCHER_TOWER_H / 130.0
        return wx, wy

    def _resolve_aim_direction(self) -> Tuple[str, bool]:
        """Определяет направление юнита (U/D/S) и горизонтальное отражение по вектору цели."""
        dx, dy = self.aim_dx, self.aim_dy
        if abs(dy) > abs(dx) * 1.15:
            return ("D" if dy >= 0 else "U"), False
        return "S", (dx > 0)

    def update(
        self,
        dt: float,
        enemies: List[Enemy],
        projectiles: List[Projectile],
        on_kill_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """Обновляет анимации, ищет цель в радиусе и выпускает стрелу или магическую сферу."""
        self.idle_timer += dt
        if self.upgrade_anim_timer > 0.0:
            self.upgrade_anim_timer = max(0.0, self.upgrade_anim_timer - dt)
        if self.attack_anim_timer > 0.0:
            self.attack_anim_timer = max(0.0, self.attack_anim_timer - dt)
        if self.attack_timer > 0.0:
            self.attack_timer = max(0.0, self.attack_timer - dt)

        best_target = None
        best_progress = -1
        for enemy in enemies:
            if enemy.is_alive and not enemy.reached_castle:
                dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
                if dist <= self.attack_range and enemy.current_wp_idx > best_progress:
                    best_progress = enemy.current_wp_idx
                    best_target = enemy

        self.has_target = best_target is not None
        if best_target:
            self.aim_dx = best_target.x - self.x
            self.aim_dy = best_target.y - self.y

            if self.attack_timer <= 0.0:
                self.attack_timer = self.cooldown
                self.attack_anim_timer = self.ATTACK_ANIM_DURATION

                vis_cfg = _TOWER_VISUAL_CFG.get(self.tower_type, _TOWER_VISUAL_CFG["archer"])
                play_sound(vis_cfg["sound"], 0.48 if self.tower_type == "mage" else 0.50)

                anchors = vis_cfg["anchors"].get(self.level, [])
                if anchors:
                    self._active_unit_idx = (self._active_unit_idx + 1) % len(anchors)
                spawn_x, spawn_y = self._get_projectile_spawn_pos(anchors)
                unit_tier = vis_cfg["unit_tier"].get(self.level, 1)

                proj = Projectile(
                    start_pos=(spawn_x, spawn_y),
                    target=best_target,
                    p_type=self.projectile_type,
                    damage=self.damage,
                    splash_radius=self.splash_radius,
                    slow_ratio=self.slow_ratio,
                    slow_duration=self.slow_duration,
                    ignore_armor=self.ignore_armor,
                    proj_tier=unit_tier,
                    on_kill=on_kill_callback,
                )
                projectiles.append(proj)

    def draw_range(self, surface: pygame.Surface) -> None:
        """Отрисовывает полупрозрачный радиус атаки при наведении и выборе."""
        if self.is_hovered or self.is_selected:
            r = int(self.attack_range)
            range_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            fill_col = (self.color[0], self.color[1], self.color[2], 35)
            pygame.draw.circle(range_surf, fill_col, (r + 1, r + 1), r)
            stroke_col = (self.color[0], self.color[1], self.color[2], 160)
            pygame.draw.circle(range_surf, stroke_col, (r + 1, r + 1), r, 1)
            surface.blit(range_surf, (int(self.x - r - 1), int(self.y - r - 1)))

    def _draw_rooftop_units(self, surface: pygame.Surface, draw_x: int, draw_y: int) -> None:
        """Отрисовывает юнитов (лучников или магов) на крыше с направлением U/D/S и состоянием атаки."""
        vis_cfg = _TOWER_VISUAL_CFG.get(self.tower_type, _TOWER_VISUAL_CFG["archer"])
        tier = vis_cfg["unit_tier"].get(self.level, 1)
        anchors = vis_cfg["anchors"].get(self.level, [])
        if not anchors:
            return

        dir_key, flip_x = self._resolve_aim_direction()
        foot_offset_y = round(33 * ARCHER_UNIT_SIZE / 48.0)

        for idx, (raw_cx, raw_fy, raw_clip_y) in enumerate(anchors):
            is_firing_unit = (len(anchors) == 1) or (idx == self._active_unit_idx)
            frames: List[pygame.Surface] = []
            f_idx = 0

            if is_firing_unit and self.attack_anim_timer > 0.0:
                frames = get_tower_unit_frames(self.tower_type, tier, dir_key, "Attack", flip_x)
                if frames:
                    progress = 1.0 - (self.attack_anim_timer / self.ATTACK_ANIM_DURATION)
                    f_idx = min(len(frames) - 1, max(0, int(progress * len(frames))))
            elif is_firing_unit and self.has_target and self.attack_timer <= self.PREATTACK_WINDOW:
                frames = get_tower_unit_frames(self.tower_type, tier, dir_key, "Preattack", flip_x)

            if not frames:
                frames = get_tower_unit_frames(self.tower_type, tier, dir_key, "Idle", flip_x)
                f_idx = int((self.idle_timer + idx * 0.25) * 5.0) % max(1, len(frames))

            if not frames:
                continue

            unit_surf = frames[f_idx]
            ux = draw_x + round(raw_cx * ARCHER_TOWER_W / 70.0) - ARCHER_UNIT_SIZE // 2
            uy = draw_y + round(raw_fy * ARCHER_TOWER_H / 130.0) - foot_offset_y
            clip_y = draw_y + round(raw_clip_y * ARCHER_TOWER_H / 130.0)
            vis_h = max(0, min(ARCHER_UNIT_SIZE, clip_y - uy))
            if vis_h > 0:
                surface.blit(unit_surf, (ux, uy), (0, 0, ARCHER_UNIT_SIZE, vis_h))

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовывает башню, юнитов на вершине и золотые звёздочки уровня (1-7)."""
        self.draw_range(surface)
        draw_x, draw_y = self._get_tower_top_left()

        if self.upgrade_anim_timer > 0.0:
            upg_frames = get_tower_upgrade_frames(self.tower_type, self.level)
            if upg_frames:
                progress = 1.0 - (self.upgrade_anim_timer / self.UPGRADE_ANIM_DURATION)
                f_idx = min(len(upg_frames) - 1, max(0, int(progress * len(upg_frames))))
                surface.blit(upg_frames[f_idx], (draw_x, draw_y))
        else:
            idle_frames = get_tower_idle_frames(self.tower_type, self.level)
            if idle_frames:
                f_idx = int(self.idle_timer * 6.0) % len(idle_frames)
                surface.blit(idle_frames[f_idx], (draw_x, draw_y))
            self._draw_rooftop_units(surface, draw_x, draw_y)

        vis_cfg = _TOWER_VISUAL_CFG.get(self.tower_type, _TOWER_VISUAL_CFG["archer"])
        top_y = vis_cfg["top_y"].get(self.level, 35)
        star_y = draw_y + round(top_y * ARCHER_TOWER_H / 130.0) - 5
        star_gold = (255, 215, 60)
        star_dark = (45, 30, 15)
        spacing = 5
        start_x = int(self.x - ((self.level - 1) * spacing) / 2.0)
        for i in range(self.level):
            sx = start_x + i * spacing
            pygame.draw.circle(surface, star_dark, (sx, star_y), 3)
            pygame.draw.circle(surface, star_gold, (sx, star_y), 2)


# ==============================================================
# ВСПЛЫВАЮЩЕЕ МЕНЮ ПОСТРОЙКИ И АПГРЕЙДА (ЛУЧНИКИ И МАГИ)
# ==============================================================

class TowerMenu:
    """Компактное контекстное меню, всплывающее над площадкой или башней."""

    def __init__(self):
        self.is_open = False
        self.mode = "build"  # "build" или "upgrade"
        self.spot_coord: Optional[Tuple[int, int]] = None
        self.selected_tower: Optional[Tower] = None
        self.anchor_x = 0
        self.anchor_y = 0

        self.font_title = get_font(13)
        self.font_btn = get_font(12)
        self.hovered_btn = None
        self.buttons: List[Dict] = []
        self.menu_rect = pygame.Rect(0, 0, 100, 80)

    def open_for_spot(
        self,
        spot_coord: Tuple[int, int],
        anchor_x: Optional[int] = None,
        anchor_y: Optional[int] = None,
    ) -> None:
        """Открывает меню постройки (Лучники и Маги) над пустой площадкой."""
        self.is_open = True
        self.mode = "build"
        self.spot_coord = spot_coord
        self.selected_tower = None

        if anchor_x is not None and anchor_y is not None:
            self.anchor_x = int(anchor_x)
            self.anchor_y = int(anchor_y)
        else:
            c, r = spot_coord
            self.anchor_x = MAP_OFFSET_X + c * TILE_SIZE + TILE_SIZE // 2
            self.anchor_y = MAP_OFFSET_Y + r * TILE_SIZE

        self._setup_build_buttons()

    def open_build(self, spot_coord: Tuple[int, int]) -> None:
        self.open_for_spot(spot_coord)

    def open_for_tower(
        self,
        tower: Tower,
        spot_coord: Optional[Tuple[int, int]] = None,
        anchor_x: Optional[int] = None,
        anchor_y: Optional[int] = None,
    ) -> None:
        """Открывает меню апгрейда / продажи над построенной башней."""
        self.is_open = True
        self.mode = "upgrade"
        self.spot_coord = spot_coord if spot_coord is not None else tower.grid_pos
        self.selected_tower = tower

        if anchor_x is not None and anchor_y is not None:
            self.anchor_x = int(anchor_x)
            self.anchor_y = int(anchor_y)
        else:
            self.anchor_x = int(tower.x)
            self.anchor_y = int(tower.y - 28)

        self._setup_upgrade_buttons()

    def open_upgrade(self, tower: Tower) -> None:
        self.open_for_tower(tower)

    def close(self) -> None:
        self.is_open = False
        self.spot_coord = None
        self.selected_tower = None
        self.hovered_btn = None
        self.buttons.clear()

    def _setup_build_buttons(self) -> None:
        """Настраивает кнопки постройки Башни лучников и Башни магов с ценой."""
        self.buttons.clear()
        menu_w, menu_h = 264, 96
        bx = max(16, min(VIRTUAL_WIDTH - menu_w - 16, self.anchor_x - menu_w // 2))
        by = max(16, min(VIRTUAL_HEIGHT - menu_h - 16, self.anchor_y - menu_h - 10))
        self.menu_rect = pygame.Rect(bx, by, menu_w, menu_h)

        specs = [("archer", "Лучники"), ("mage", "Маги")]
        btn_w, btn_h = 116, 60
        for idx, (t_type, label) in enumerate(specs):
            if t_type not in TOWERS:
                continue
            lvl1 = TOWERS[t_type]["levels"][1]
            btn_x = bx + 10 + idx * (btn_w + 12)
            self.buttons.append({
                "action": "build",
                "tower_type": t_type,
                "label": label,
                "cost": lvl1["cost"],
                "range": lvl1["range"],
                "color": TOWERS[t_type]["color"],
                "rect": pygame.Rect(btn_x, by + 26, btn_w, btn_h),
            })

    def _setup_upgrade_buttons(self) -> None:
        """Настраивает кнопки [Апгрейд] и [Продать] над построенной башней."""
        self.buttons.clear()
        menu_w, menu_h = 210, 88
        bx = max(16, min(VIRTUAL_WIDTH - menu_w - 16, self.anchor_x - menu_w // 2))
        by = max(16, min(VIRTUAL_HEIGHT - menu_h - 16, self.anchor_y - menu_h - 10))
        self.menu_rect = pygame.Rect(bx, by, menu_w, menu_h)

        t = self.selected_tower
        if not t:
            return

        btn_w, btn_h = 92, 54
        self.buttons.append({
            "action": "upgrade",
            "can_upgrade": t.can_upgrade,
            "cost": t.upgrade_cost,
            "rect": pygame.Rect(bx + 10, by + 25, btn_w, btn_h),
            "next_range": TOWERS[t.tower_type]["levels"][t.level + 1]["range"] if t.can_upgrade else t.attack_range,
            "color": (90, 210, 105),
        })

        self.buttons.append({
            "action": "sell",
            "refund": t.sell_refund,
            "rect": pygame.Rect(bx + 108, by + 25, btn_w, btn_h),
            "color": (225, 85, 70),
        })

    def update_hover(self, vx: int, vy: int) -> None:
        self.hovered_btn = None
        if not self.is_open:
            return
        for btn in self.buttons:
            if btn["rect"].collidepoint(vx, vy):
                self.hovered_btn = btn
                break

    def handle_click(self, vx: int, vy: int, gold: int) -> Dict:
        if not self.is_open:
            return {"action": "none"}

        for btn in self.buttons:
            if btn["rect"].collidepoint(vx, vy):
                act = btn["action"]
                if act == "build":
                    if gold >= btn["cost"]:
                        res = {
                            "action": "build",
                            "tower_type": btn["tower_type"],
                            "cost": btn["cost"],
                            "spot": self.spot_coord,
                        }
                        self.close()
                        return res
                    return {"action": "cant_afford"}

                elif act == "upgrade":
                    if btn["can_upgrade"]:
                        if gold >= btn["cost"]:
                            res = {
                                "action": "upgrade",
                                "tower": self.selected_tower,
                                "cost": btn["cost"],
                            }
                            self.close()
                            return res
                        return {"action": "cant_afford"}

                elif act == "sell":
                    res = {
                        "action": "sell",
                        "tower": self.selected_tower,
                        "refund": btn["refund"],
                        "spot": self.spot_coord,
                    }
                    self.close()
                    return res

        if not self.menu_rect.collidepoint(vx, vy):
            self.close()
            return {"action": "close"}

        return {"action": "none"}

    def _draw_build_icon(self, surface: pygame.Surface, tower_type: str, rect: pygame.Rect) -> None:
        """Отрисовывает чёткую мини-иконку башни внутри кнопки постройки."""
        vis_cfg = _TOWER_VISUAL_CFG.get(tower_type, _TOWER_VISUAL_CFG["archer"])
        pack_type, tier, crop_rect = vis_cfg["menu_icon"]
        frames = get_tower_idle_frames(pack_type, tier)
        if not frames:
            return
        src = frames[0]
        cx, cy, cw, ch = crop_rect
        cx = max(0, min(src.get_width() - 1, cx))
        cy = max(0, min(src.get_height() - 1, cy))
        cw = min(cw, src.get_width() - cx)
        ch = min(ch, src.get_height() - cy)
        crop = src.subsurface((cx, cy, cw, ch))
        target_h = 44
        target_w = max(24, min(36, int(round(cw * target_h / max(1, ch)))))
        mini_icon = pygame.transform.scale(crop, (target_w, target_h))
        surface.blit(mini_icon, (rect.x + 5, rect.y + (rect.h - target_h) // 2))

    def draw(self, surface: pygame.Surface, current_gold: int) -> None:
        if not self.is_open:
            return

        if self.hovered_btn:
            preview_range = self.hovered_btn.get("range") or self.hovered_btn.get("next_range")
            if preview_range:
                r = int(preview_range)
                col = self.hovered_btn.get("color", (255, 255, 255))
                range_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(range_surf, (col[0], col[1], col[2], 40), (r + 1, r + 1), r)
                pygame.draw.circle(range_surf, (col[0], col[1], col[2], 180), (r + 1, r + 1), r, 1)
                surface.blit(range_surf, (self.anchor_x - r - 1, self.anchor_y - r - 1))

        s_surf = pygame.Surface((self.menu_rect.w, self.menu_rect.h), pygame.SRCALPHA)
        s_surf.fill((0, 0, 0, 150))
        surface.blit(s_surf, (self.menu_rect.x + 2, self.menu_rect.y + 2))

        pygame.draw.rect(surface, (28, 20, 16), self.menu_rect)
        pygame.draw.rect(surface, (205, 165, 75), self.menu_rect, 1)

        if self.mode == "build":
            title_text = "ПОСТРОЙКА"
        else:
            t = self.selected_tower
            title_text = f"{t.level_name if t else 'БАШНЯ'}"

        t_surf = self.font_title.render(title_text, True, (255, 235, 165))
        tx = self.menu_rect.x + (self.menu_rect.w - t_surf.get_width()) // 2
        surface.blit(t_surf, (tx, self.menu_rect.y + 4))

        for btn in self.buttons:
            rect = btn["rect"]
            is_hover = (btn == self.hovered_btn)
            act = btn["action"]

            if act == "build":
                affordable = current_gold >= btn["cost"]
                bg_col = (52, 40, 26) if affordable else (32, 24, 20)
                border_col = (255, 225, 95) if (is_hover and affordable) else ((165, 125, 60) if affordable else (75, 60, 48))

                pygame.draw.rect(surface, bg_col, rect)
                pygame.draw.rect(surface, border_col, rect, 1)

                self._draw_build_icon(surface, btn["tower_type"], rect)

                text_cx = rect.x + 76
                lbl_col = (255, 245, 220) if affordable else (135, 125, 115)
                lbl = self.font_btn.render(btn["label"], True, lbl_col)
                surface.blit(lbl, (text_cx - lbl.get_width() // 2, rect.y + 11))

                cost_col = (255, 215, 60) if affordable else (195, 70, 70)
                cost_lbl = self.font_btn.render(f"{btn['cost']}g", True, cost_col)
                surface.blit(cost_lbl, (text_cx - cost_lbl.get_width() // 2, rect.y + 32))

            elif act == "upgrade":
                can_upg = btn["can_upgrade"]
                affordable = can_upg and (current_gold >= btn["cost"])
                bg_col = (30, 48, 28) if affordable else (24, 28, 24)
                border_col = (110, 235, 125) if (is_hover and affordable) else ((80, 160, 90) if affordable else (60, 70, 60))

                pygame.draw.rect(surface, bg_col, rect)
                pygame.draw.rect(surface, border_col, rect, 1)

                if can_upg:
                    lbl = self.font_btn.render("Апгрейд", True, (225, 255, 225) if affordable else (125, 140, 125))
                    surface.blit(lbl, (rect.x + (rect.w - lbl.get_width()) // 2, rect.y + 10))
                    cost_col = (255, 215, 60) if affordable else (195, 70, 70)
                    cost_lbl = self.font_btn.render(f"+{btn['cost']}g", True, cost_col)
                    surface.blit(cost_lbl, (rect.x + (rect.w - cost_lbl.get_width()) // 2, rect.y + 30))
                else:
                    lbl = self.font_btn.render("MAX Lvl", True, (160, 175, 160))
                    surface.blit(lbl, (rect.x + (rect.w - lbl.get_width()) // 2, rect.y + 19))

            elif act == "sell":
                bg_col = (52, 28, 24) if is_hover else (38, 22, 20)
                border_col = (235, 95, 80) if is_hover else (160, 65, 55)

                pygame.draw.rect(surface, bg_col, rect)
                pygame.draw.rect(surface, border_col, rect, 1)

                lbl = self.font_btn.render("Продать", True, (255, 215, 210))
                surface.blit(lbl, (rect.x + (rect.w - lbl.get_width()) // 2, rect.y + 10))

                ref_lbl = self.font_btn.render(f"+{btn['refund']}g", True, (255, 215, 60))
                surface.blit(ref_lbl, (rect.x + (rect.w - ref_lbl.get_width()) // 2, rect.y + 30))
