"""
Автоматизированный модульный тест для проверки базовой боевой системы командира (Этап 5):
- Базовые характеристики и PNG-анимации (без старых навыков Q/W/пассивки)
- Автоатака ближнего боя
- Начисление опыта и повышение уровня
- Карточка персонажа [C]
- Гибель героя, 30% штраф золота и таймер возрождения
- Агр врагов на командира (лимит 3, распределение по дуге, сброс агра)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame

from entities.hero import Hero
from entities.enemy import Enemy
from core.wave_manager import WaveManager
from ui.character_card import CharacterCard
from vfx.particles import ParticleSystem
from vfx.floating_text import FloatingTextManager
from vfx.camera import CameraShake


def test_stage5():
    pygame.init()
    pygame.font.init()

    hero = Hero(start_grid_pos=(10, 8))
    dummy_waypoints = [(hero.x, hero.y), (hero.x + 20, hero.y)]

    particle_sys = ParticleSystem()
    floating_texts = FloatingTextManager()
    cam_shake = CameraShake()
    char_card = CharacterCard()

    # 1. Проверка базовых характеристик (без навыков Q/W/пассивки)
    assert hero.is_alive
    assert hero.level == 1
    assert hero.hp == hero.max_hp
    assert not hasattr(hero, "use_skill_q")
    assert not hasattr(hero, "use_skill_w")
    assert len(hero.idle_frames) == 8
    assert len(hero.walk_frames) == 6
    assert len(hero.attack1_frames) == 4
    assert len(hero.attack2_frames) == 4
    assert len(hero.attack_frames) == 4
    idle_fig_h = hero.idle_frames[0].get_bounding_rect(min_alpha=10).h
    assert 34 <= idle_fig_h <= 42, f"Ожидался рост рыцаря 34..42 px, получено {idle_fig_h}"

    # 2. Проверка автоатаки героя
    enemy = Enemy("goblin", waypoints=dummy_waypoints, wave_index=0)
    enemy.x, enemy.y = hero.x + 22, hero.y
    init_hp = enemy.hp

    hero.update(
        0.1,
        enemies=[enemy],
        particle_sys=particle_sys,
        floating_texts=floating_texts,
        cam_shake=cam_shake,
    )
    assert enemy.hp < init_hp, f"Враг должен получить урон от автоатаки! {enemy.hp} vs {init_hp}"
    assert hero.attack_timer > 0.0, "Должен запуститься кулдаун атаки героя"
    assert len(particle_sys.particles) > 0, "Должны появиться искры удара"
    assert len(floating_texts.texts) > 0, "Должен появиться всплывающий урон"

    # 3. Проверка опыта и повышения уровня
    prev_dmg = hero.attack_damage
    prev_max_hp = hero.max_hp
    hero.add_xp(80, particle_sys=particle_sys, floating_texts=floating_texts)
    assert hero.level == 2, f"Уровень героя должен вырасти до 2, сейчас: {hero.level}"
    assert hero.max_hp > prev_max_hp
    assert hero.attack_damage > prev_dmg

    # 4. Проверка открытия и закрытия карточки персонажа [C]
    char_card.open()
    assert char_card.is_open
    from settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT
    surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    char_card.draw(surf, hero)
    assert char_card.handle_click(char_card.btn_close_rect.centerx, char_card.btn_close_rect.centery, hero)
    assert not char_card.is_open

    # 5. Проверка гибели и возрождения героя со штрафом золота
    mock_wm = WaveManager([(0, 0), (1, 0)])
    mock_wm.gold = 300
    hero.take_damage(9999, particle_sys, floating_texts, wave_manager=mock_wm, cam_shake=cam_shake)
    assert not hero.is_alive, "Герой должен погибнуть при получении смертельного урона"
    assert hero.respawn_timer > 0.0, "Должен запуститься таймер возрождения"
    assert mock_wm.gold == 210, f"Золото должно уменьшиться на 30% (штраф): было 300, стало {mock_wm.gold}"

    hero.update(13.0, particle_sys=particle_sys, floating_texts=floating_texts)
    assert hero.is_alive, "Герой должен возродиться после завершения таймера"
    assert hero.hp == hero.max_hp, "HP должно полностью восстановиться"
    assert (hero.x, hero.y) == (hero.start_x, hero.start_y), "Герой должен возродиться у лагеря"

    # 6. Проверка механики агра врагов на командира (максимум 2 врага, статичные слоты без кружения)
    import math
    hero.hp = float(hero.max_hp)
    aggro_wm = WaveManager([(0, 0), (10, 0), (20, 0)])
    enemies_pool = []
    for i in range(5):
        e = Enemy("goblin", waypoints=[(hero.x - 40 + i * 5, hero.y), (hero.x + 150, hero.y)], wave_index=0)
        e.x = hero.x - 40 + i * 5
        e.y = hero.y
        enemies_pool.append(e)
    aggro_wm.enemies = enemies_pool

    aggro_wm.update(0.1, hero=hero, particle_sys=particle_sys, floating_texts=floating_texts)

    engaged = [e for e in aggro_wm.enemies if e.is_engaged]
    non_engaged = [e for e in aggro_wm.enemies if not e.is_engaged]
    assert len(engaged) == 2, f"На героя должно заагриться максимум 2 врага, сейчас: {len(engaged)}"
    assert len(non_engaged) == 3, f"Остальные 3 врага должны идти мимо, сейчас: {len(non_engaged)}"

    # Даём 2 заагренным врагам дойти до своих статичных слотов (25 px), а 3 свободным — пройти дальше
    non_engaged_start_x = [e.x for e in non_engaged]
    for _ in range(25):
        hero.hp = float(hero.max_hp)
        aggro_wm.update(0.05, hero=hero, particle_sys=particle_sys, floating_texts=floating_texts)

    assert all(e.in_melee_stance for e in engaged), "Заагренные враги должны остановиться в точке боя"
    assert all(e.x > sx + 20.0 for e, sx in zip(non_engaged, non_engaged_start_x)), "Незаагренные враги должны идти вперёд по дороге"

    positions = set((round(e.x, 1), round(e.y, 1)) for e in engaged)
    assert len(positions) == 2, "Заагренные враги должны стоять в двух разных статичных слотах"
    for e in engaged:
        dist_h = math.hypot(e.x - hero.x, e.y - hero.y)
        assert 22.0 <= dist_h <= 28.0, f"Ожидалась дистанция боя ~25 px, сейчас: {dist_h}"

    # Проверяем отсутствие кружения/дёргания: за следующую 1.0 сек координаты не меняются
    locked_coords = [(e.x, e.y) for e in engaged]
    for _ in range(20):
        hero.hp = float(hero.max_hp)
        aggro_wm.update(0.05, hero=hero, particle_sys=particle_sys, floating_texts=floating_texts)
    assert [(e.x, e.y) for e in engaged] == locked_coords, "Враги в слоте не должны кружить или дёргаться"

    # Небольшой шаг героя на 5 px (< 9 px) не срывает стойку; отход > 10 px запускает преследование
    hero.x += 5.0
    aggro_wm.update(0.05, hero=hero, particle_sys=particle_sys, floating_texts=floating_texts)
    assert all(e.in_melee_stance for e in engaged), "Мёртвая зона отхода <= 9 px не должна сбивать стойку"

    hero.x += 12.0
    aggro_wm.update(0.05, hero=hero, particle_sys=particle_sys, floating_texts=floating_texts)
    assert all(not e.in_melee_stance for e in engaged), "При отходе героя > 9 px враги должны догнать слот"

    # Отвод героя > 105 px от всех врагов сбрасывает агр
    hero.y += 200
    aggro_wm.update(0.1, hero=hero, particle_sys=particle_sys, floating_texts=floating_texts)
    engaged_after_retreat = [e for e in aggro_wm.enemies if e.is_engaged]
    assert len(engaged_after_retreat) == 0, "Все враги должны сбросить агр при отходе героя > 105px"

    hero.x, hero.y = aggro_wm.enemies[0].x + 20, aggro_wm.enemies[0].y
    aggro_wm.update(0.1, hero=hero, particle_sys=particle_sys, floating_texts=floating_texts)
    assert any(e.is_engaged for e in aggro_wm.enemies), "Враги должны снова заагриться на живого героя"

    hero.is_alive = False
    aggro_wm.update(0.1, hero=hero, particle_sys=particle_sys, floating_texts=floating_texts)
    engaged_after_death = [e for e in aggro_wm.enemies if e.is_engaged]
    assert len(engaged_after_death) == 0, "После гибели героя все враги должны сбросить агр"

    print("ВСЕ ТЕСТЫ ЭТАПА 5 (ВКЛЮЧАЯ АГР И БЛОКИРОВКУ) УСПЕШНО ПРОЙДЕНЫ!")
    pygame.quit()


if __name__ == "__main__":
    test_stage5()
