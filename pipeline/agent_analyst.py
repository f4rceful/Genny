"""Агент-аналитик: генерирует НФТ (нефункциональные требования) и ФТ (функциональные требования)."""
import os
import re
from jinja2 import Environment, FileSystemLoader
from utils.llm_client import call_llm, get_model
from utils.file_writer import write_artifact

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")
_jinja_env = Environment(loader=FileSystemLoader(_PROMPTS_DIR))


def _strip_doc_header(text: str) -> str:
    """Убирает заголовок вида '### non-functional-req.md', который иногда добавляет модель."""
    lines = text.splitlines()
    if lines and re.match(r"^#+\s*(non-functional-req|functional-req|use-cases)\.md", lines[0], re.IGNORECASE):
        text = "\n".join(lines[1:]).lstrip("\n")
    return text


def run(bt: str, bp: str, features: str, run_id: str, use_cases: str = "") -> dict:
    """Генерирует docs/non-functional-req.md и docs/functional-req.md.

    Ожидает в ответе модели маркер ---SPLIT--- для разделения НФТ и ФТ.
    """
    print("[AgentAnalyst] starting...")

    template = _jinja_env.get_template("analyst.j2")
    user_prompt = template.render(bt=bt, bp=bp, features=features, use_cases=use_cases)

    system_prompt = (
        "Ты опытный бизнес-аналитик программного обеспечения. "
        "Отвечай строго на русском языке. "
        "Соблюдай структуру и маркеры, указанные в задании."
    )

    response = call_llm(system=system_prompt, user=user_prompt, model=get_model("analyst"), run_id=run_id)

    # Модель должна разделить НФТ и ФТ маркером ---SPLIT---
    parts = response.split("---SPLIT---", maxsplit=1)
    if len(parts) == 2:
        non_functional_req = _strip_doc_header(parts[0].strip())
        functional_req = _strip_doc_header(parts[1].strip())
    else:
        # если модель не вставила маркер, считаем весь текст НФТ
        print("[AgentAnalyst] WARNING: ---SPLIT--- marker not found in response, using full text as NFR")
        non_functional_req = response.strip()
        functional_req = response.strip()

    write_artifact(run_id, "docs/non-functional-req.md", non_functional_req)
    write_artifact(run_id, "docs/functional-req.md", functional_req)

    print(f"[AgentAnalyst] done, wrote: docs/non-functional-req.md, docs/functional-req.md")
    return {
        "non_functional_req": non_functional_req,
        "functional_req": functional_req,
    }


def _parse_docs(response: str) -> dict[str, str]:
    """Парсит ответ с маркерами ---DOC: имя--- в словарь {имя_файла: содержимое}."""
    docs: dict[str, str] = {}
    pattern = r"---DOC:\s*(.+?)---\n(.*?)(?=---DOC:|$)"
    for name, content in re.findall(pattern, response, re.DOTALL):
        docs[name.strip()] = content.strip()
    return docs


def patch(instruction: str, run_id: str) -> list[str]:
    """Обновляет docs/ по инструкции пользователя и возвращает список изменённых файлов."""
    print(f"[AgentAnalyst:patch] instruction: {instruction!r}")

    docs_dir = os.path.join("output", run_id, "docs")

    def _read(name: str) -> str:
        try:
            with open(os.path.join(docs_dir, name), encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    non_functional_req = _read("non-functional-req.md")
    functional_req = _read("functional-req.md")
    use_cases = _read("use-cases.md")

    if not non_functional_req and not functional_req:
        print("[AgentAnalyst:patch] WARNING: no docs found, skipping")
        return []

    template = _jinja_env.get_template("docs_patcher.j2")
    user_prompt = template.render(
        instruction=instruction,
        non_functional_req=non_functional_req,
        functional_req=functional_req,
        use_cases=use_cases,
    )

    system_prompt = (
        "Ты опытный бизнес-аналитик. "
        "Вноси только минимально необходимые изменения в документацию. "
        "Строго соблюдай маркеры ---DOC: name---. "
        "Отвечай строго на русском языке."
    )

    response = call_llm(system=system_prompt, user=user_prompt, model=get_model("analyst"), run_id=run_id)
    updated = _parse_docs(response)

    written: list[str] = []
    for doc_name, content in updated.items():
        write_artifact(run_id, f"docs/{doc_name}", content)
        written.append(f"docs/{doc_name}")

    print(f"[AgentAnalyst:patch] updated: {written}")
    return written
