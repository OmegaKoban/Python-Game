"""
Система рекордов: сохранение и загрузка топ-10 результатов в JSON.
"""

import json
import os


RECORDS_FILE = os.path.join(os.path.dirname(__file__), "..", "records.json")
MAX_RECORDS = 10


def load_records():
    """
    Загружает список рекордов из файла.
    Возвращает список словарей:
    [{"name": str, "kills": int, "waves": int, "time": float}, ...]
    Отсортирован по убийствам (descending).
    """
    if not os.path.exists(RECORDS_FILE):
        return []
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def save_records(records):
    """Сохраняет список рекордов в файл."""
    try:
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def add_record(name, kills, waves):
    """
    Добавляет новый рекорд. Сортирует по убийствам (descending),
    оставляет топ-10.
    """
    records = load_records()
    records.append({
        "name": name,
        "kills": kills,
        "waves": waves,
    })
    # Сортировка: сначала по убийствам (больше = лучше), при равенстве — по волнам.
    records.sort(key=lambda r: (-r["kills"], -r["waves"]))
    records = records[:MAX_RECORDS]
    save_records(records)
