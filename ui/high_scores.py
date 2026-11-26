"""
Модуль таблицы рекордов (High Scores) — Этап 6.
Управляет:
- Подсчётом финального счёта (Score) по формуле из дизайн-документа:
  Score = (HP Замка * 150) + (Золото * 2) + (Убито врагов * 10) + (Пройдено волн * 500)
- Сохранением и чтением Топ-5 лучших результатов в файл records.json
- Сортировкой, определением нового рекорда и даты достижения
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Tuple, Any

RECORDS_FILE = "records.json"

DEFAULT_RECORDS = [
    {"name": "Сэр Роланд", "score": 8500, "waves": 10, "kills": 65, "date": "2026-11-20"},
    {"name": "Лорд Гавейн", "score": 6800, "waves": 9, "kills": 54, "date": "2026-11-21"},
    {"name": "Капитан Блейк", "score": 5200, "waves": 8, "kills": 42, "date": "2026-11-21"},
    {"name": "Страж Артур", "score": 3900, "waves": 6, "kills": 30, "date": "2026-11-22"},
    {"name": "Оруженосец Джон", "score": 2400, "waves": 4, "kills": 18, "date": "2026-11-22"},
]


def calculate_score(castle_hp: int, gold: int, kills: int, waves_cleared: int) -> int:
    """
    Рассчитывает итоговый счёт игры по утверждённой формуле:
    Score = (HP Замка * 150) + (Оставшееся Золото * 2) + (Убито врагов * 10) + (Пройдено волн * 500)
    """
    hp_pts = max(0, castle_hp) * 150
    gold_pts = max(0, gold) * 2
    kill_pts = max(0, kills) * 10
    wave_pts = max(0, waves_cleared) * 500
    return hp_pts + gold_pts + kill_pts + wave_pts


def load_records() -> List[Dict[str, Any]]:
    """Загружает список рекордов из records.json или создаёт значения по умолчанию."""
    if not os.path.exists(RECORDS_FILE):
        save_records(DEFAULT_RECORDS)
        return list(DEFAULT_RECORDS)

    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                # Сортировка по убыванию счёта
                data.sort(key=lambda r: r.get("score", 0), reverse=True)
                return data[:5]
    except Exception as e:
        print(f"[HighScores] Ошибка чтения {RECORDS_FILE}: {e}. Используем дефолтные рекорды.")

    return list(DEFAULT_RECORDS)


def save_records(records: List[Dict[str, Any]]) -> None:
    """Сохраняет список рекордов в файл records.json (только Топ-5)."""
    try:
        top_5 = sorted(records, key=lambda r: r.get("score", 0), reverse=True)[:5]
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(top_5, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[HighScores] Ошибка записи в {RECORDS_FILE}: {e}")


def add_record(
    name: str, castle_hp: int, gold: int, kills: int, waves_cleared: int
) -> Tuple[int, bool, int, Dict[str, Any]]:
    """
    Добавляет результат текущей игры в таблицу рекордов:
    Возвращает (итоговый_счёт, вошёл_ли_в_топ5, занятое_место_1_to_5_или_0, запись).
    """
    score = calculate_score(castle_hp, gold, kills, waves_cleared)
    date_str = datetime.now().strftime("%Y-%m-%d")

    new_entry = {
        "name": name,
        "score": score,
        "waves": waves_cleared,
        "kills": kills,
        "date": date_str,
    }

    current = load_records()
    current.append(new_entry)
    current.sort(key=lambda r: r.get("score", 0), reverse=True)

    # Проверяем позицию новой записи
    top_5 = current[:5]
    rank = 0
    is_top_5 = False

    for idx, r in enumerate(top_5):
        if r is new_entry:
            rank = idx + 1
            is_top_5 = True
            break

    save_records(top_5)
    return score, is_top_5, rank, new_entry
