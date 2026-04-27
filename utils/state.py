import json
import os


def _path(run_id: str) -> str:
    return os.path.join("output", run_id, ".state.json")


def write(run_id: str, status: str, step: str = "", error: str = "") -> None:
    os.makedirs(os.path.join("output", run_id), exist_ok=True)
    with open(_path(run_id), "w", encoding="utf-8") as f:
        json.dump({"status": status, "step": step, "error": error}, f, ensure_ascii=False)


def read(run_id: str) -> dict:
    try:
        with open(_path(run_id), encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"status": "running", "step": "", "error": ""}
