"""
Автоматизированный модульный тест для проверки функционала Этапа 6:
- Процедурный синтез звуков в core/sound.py (SoundManager)
- Формула подсчёта очков и сохранение в records.json (ui/high_scores.py)
- Финальные экраны Победы и Поражения (ui/end_screen.py)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from core.sound import SoundManager, get_sound_manager
from ui.high_scores import calculate_score, add_record, load_records, save_records, RECORDS_FILE
from ui.end_screen import EndScreen


def test_stage6():
    pygame.init()
    pygame.font.init()

    # 1. Проверка аудиосистемы (SoundManager)
    sound_mgr = SoundManager()
    assert len(sound_mgr.sounds) >= 11, f"Должно быть синтезировано не менее 11 звуков, сейчас: {len(sound_mgr.sounds)}"

    required_sounds = [
        "click", "coin", "arrow", "sword_hit", "magic_burst",
        "level_up", "build", "victory", "defeat", "hero_death"
    ]
    for s_name in required_sounds:
        assert s_name in sound_mgr.sounds, f"Звук '{s_name}' должен присутствовать в банке"

    # Проверка вызова без ошибок
    sound_mgr.play("click")
    sound_mgr.play("coin")
    sound_mgr.play("skill_q")

    # Проверка включения / выключения звука (Mute)
    assert not sound_mgr.is_muted
    sound_mgr.toggle_mute()
    assert sound_mgr.is_muted
    sound_mgr.play("arrow")  # Не должно падать при Mute
    sound_mgr.toggle_mute()
    assert not sound_mgr.is_muted

    # 2. Проверка формулы подсчёта очков (Score)
    # Score = (HP * 150) + (Gold * 2) + (Kills * 10) + (Waves * 500)
    score_test = calculate_score(castle_hp=15, gold=200, kills=50, waves_cleared=10)
    expected = (15 * 150) + (200 * 2) + (50 * 10) + (10 * 500)
    assert score_test == expected, f"Счёт {score_test} не совпадает с ожидаемым {expected}"
    assert score_test == 8150

    # Проверка нулевых значений
    assert calculate_score(0, 0, 0, 0) == 0

    # 3. Проверка сохранения и загрузки рекордов в records.json
    # Временно изолируем файл рекордов для чистоты теста
    backup_records = None
    if os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            backup_records = f.read()
        os.remove(RECORDS_FILE)

    try:
        test_score, is_top, rank, entry = add_record(
            name="Тестовый Рыцарь",
            castle_hp=20,
            gold=500,
            kills=80,
            waves_cleared=10,
        )
        # 20*150=3000, 500*2=1000, 80*10=800, 10*500=5000 -> Итого 9800
        assert test_score == 9800
        assert is_top, "Результат 9800 должен войти в Топ-5"
        assert rank == 1, f"Результат 9800 должен стать рекордом №1, текущий ранг: {rank}"
        assert os.path.exists(RECORDS_FILE), "Файл records.json должен быть создан на диске"

        records = load_records()
        assert len(records) <= 5, "В таблице рекордов должно быть не более 5 записей"
        assert records[0]["score"] >= records[1]["score"], "Рекорды должны быть отсортированы по убыванию"
    finally:
        # Восстанавливаем файл рекордов после теста
        if backup_records is not None:
            with open(RECORDS_FILE, "w", encoding="utf-8") as f:
                f.write(backup_records)

    # 4. Проверка экрана завершения игры (EndScreen)
    end_scr = EndScreen()
    assert not end_scr.is_active

    # Тест победы
    end_scr.show(
        outcome="victory",
        hero_name="Рыцарь-командир",
        castle_hp=18,
        gold=350,
        kills=60,
        waves_cleared=10,
    )
    assert end_scr.is_active
    assert end_scr.outcome == "victory"
    assert end_scr.stats["score"] > 0

    # Отрисовка на виртуальном Surface 720x540 без ошибок
    from settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT
    v_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    end_scr.draw(v_surf)

    # Проверка клика по кнопке "Заново"
    bx = end_scr.btn_restart_rect.centerx
    by = end_scr.btn_restart_rect.centery
    clicked = end_scr.handle_click(bx, by)
    assert clicked, "Клик по кнопке 'Заново' должен вернуть True"
    assert not end_scr.is_active, "Экран должен закрыться после нажатия 'Заново'"

    # Тест поражения
    end_scr.show(
        outcome="defeat",
        hero_name="Рыцарь-командир",
        castle_hp=0,
        gold=120,
        kills=25,
        waves_cleared=4,
    )
    assert end_scr.is_active
    assert end_scr.outcome == "defeat"
    end_scr.draw(v_surf)

    print("ВСЕ ТЕСТЫ ЭТАПА 6 УСПЕШНО ПРОЙДЕНЫ!")
    pygame.quit()


if __name__ == "__main__":
    test_stage6()
