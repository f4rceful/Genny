import os


def write_artifact(run_id: str, relative_path: str, content: str) -> str:
    """Write content to output/{run_id}/{relative_path}, creating dirs as needed.
    Returns the full path written."""
    full_path = os.path.join("output", run_id, relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return full_path
