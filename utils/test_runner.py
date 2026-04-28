"""Запуск pytest для сгенерированных тестов приложения."""
import os
import subprocess
import sys


def run_tests(run_id: str) -> dict:
    """Запускает pytest в output/{run_id}/tests/ и возвращает {passed, output, returncode}."""
    tests_dir = os.path.join("output", run_id, "tests")
    if not os.path.isdir(tests_dir):
        return {"passed": False, "output": "tests/ directory not found", "returncode": -1}

    result = subprocess.run(
        [sys.executable, "-m", "pytest", tests_dir, "-v", "--tb=short", "--no-header", "-q",
         "--timeout=10"],
        capture_output=True,
        text=True,
        timeout=120,  # жёсткий лимит на случай зависания тестов
    )

    output = result.stdout + result.stderr
    passed = result.returncode == 0
    return {"passed": passed, "output": output.strip(), "returncode": result.returncode}
