"""Состояние запуска: статус, текущий шаг и история шагов сохраняются в .state.json."""
import json
import os
import time


def _path(run_id: str) -> str:
    return os.path.join("output", run_id, ".state.json")


def write(run_id: str, status: str, step: str = "", error: str = "", model: str = "") -> None:
    """Обновляет состояние: закрывает предыдущий шаг и добавляет новый в историю шагов."""
    os.makedirs(os.path.join("output", run_id), exist_ok=True)

    existing = read(run_id)
    steps = existing.get("steps", [])
    now = time.time()

    # Закрываем предыдущий шаг — проставляем время окончания
    if steps and steps[-1].get("ended_at") is None:
        steps[-1]["ended_at"] = now

    if step:
        steps.append({
            "name": step,
            "started_at": now,
            "ended_at": None,
            "model": model,
        })

    with open(_path(run_id), "w", encoding="utf-8") as f:
        json.dump({
            "status": status,
            "step": step,
            "error": error,
            "steps": steps,
        }, f, ensure_ascii=False)


def read(run_id: str) -> dict:
    try:
        with open(_path(run_id), encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Файл может не существовать в самом начале запуска — возвращаем дефолт
        return {"status": "running", "step": "", "error": "", "steps": []}
