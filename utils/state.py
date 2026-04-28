import json
import os
import time


def _path(run_id: str) -> str:
    return os.path.join("output", run_id, ".state.json")


def write(run_id: str, status: str, step: str = "", error: str = "", model: str = "") -> None:
    os.makedirs(os.path.join("output", run_id), exist_ok=True)

    existing = read(run_id)
    steps = existing.get("steps", [])
    now = time.time()

    # Close the last open step
    if steps and steps[-1].get("ended_at") is None:
        steps[-1]["ended_at"] = now

    # Add new step
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
        return {"status": "running", "step": "", "error": "", "steps": []}
