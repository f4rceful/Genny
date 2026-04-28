"""Запись артефактов генерации в output/{run_id}/."""
import os


def write_artifact(run_id: str, relative_path: str, content: str) -> str:
    """Создаёт файл output/{run_id}/{relative_path}, создавая промежуточные директории."""
    full_path = os.path.join("output", run_id, relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return full_path
