import os
import re
from jinja2 import Environment, FileSystemLoader
from utils.llm_client import call_llm
from utils.file_writer import write_artifact

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")
_jinja_env = Environment(loader=FileSystemLoader(_PROMPTS_DIR))


def _read_all_src(run_id: str) -> str:
    """Read all source files from output/{run_id}/src/ and concatenate them with headers."""
    src_dir = os.path.join("output", run_id, "src")
    if not os.path.isdir(src_dir):
        return ""

    parts = []
    for dirpath, _, filenames in os.walk(src_dir):
        for fname in sorted(filenames):
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, src_dir)
            try:
                with open(full, encoding="utf-8") as f:
                    content = f.read()
                parts.append(f"### {rel}\n```\n{content}\n```")
            except Exception:
                pass
    return "\n\n".join(parts)


def run(functional_req: str, run_id: str, src_code: str = "") -> dict:
    print("[AgentTester] starting...")

    if not src_code:
        src_code = _read_all_src(run_id)
        if not src_code:
            print("[AgentTester] WARNING: no source files found, generating tests without source")

    template = _jinja_env.get_template("tester.j2")
    user_prompt = template.render(functional_req=functional_req, src_code=src_code)

    system_prompt = (
        "Ты опытный QA-инженер. "
        "Пиши чистый pytest-код на Python без внешних зависимостей кроме pytest. "
        "Тестируй бизнес-логику приложения, воспроизводя её на Python. "
        "Комментарии и docstring — на русском языке."
    )

    response = call_llm(system=system_prompt, user=user_prompt)

    parts = response.split("---REQUIREMENTS---", maxsplit=1)
    test_code = parts[0].strip()

    test_code = re.sub(r"^```(?:python)?\s*\n?", "", test_code, flags=re.IGNORECASE)
    test_code = re.sub(r"\n?```\s*$", "", test_code)
    test_code = test_code.strip()

    write_artifact(run_id, "tests/test_functional.py", test_code)
    print("[AgentTester] done, wrote: tests/test_functional.py")
    return {"test_file": "tests/test_functional.py"}
