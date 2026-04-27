import json
import os
import re
from jinja2 import Environment, FileSystemLoader
from utils.llm_client import call_llm, get_model
from utils.file_writer import write_artifact

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")
_jinja_env = Environment(loader=FileSystemLoader(_PROMPTS_DIR))

_SELF_CHECK_SYSTEM = (
    "Ты опытный senior frontend-разработчик и code reviewer. "
    "Получаешь набор файлов веб-приложения и чеклист проверки. "
    "Исправь ВСЕ найденные проблемы и верни файлы в том же формате с маркерами ---FILE: path---. "
    "Выводи ТОЛЬКО маркеры и содержимое файлов — никаких пояснений, никаких markdown-блоков."
)

_SELF_CHECK_PROMPT = """\
Проверь следующие файлы веб-приложения по универсальному чеклисту и исправь все найденные проблемы.

## Чеклист проверки

### 1. Чистота HTML
- `index.html` не содержит тегов `<style>` с CSS-кодом (только `<link rel="stylesheet">`)
- `index.html` не содержит тегов `<script>` с JS-кодом (только `<script src="...">`)
- Нет атрибутов `onclick`, `onchange`, `oninput` и других inline-обработчиков
- Скрипты подключены в конце `<body>` в правильном порядке зависимостей

### 2. Разделение ответственности
- Файлы с бизнес-логикой не содержат `document.`, `window.`, `querySelector`, `getElementById` — только чистые функции/классы
- Файлы с UI-логикой не содержат бизнес-вычислений — только DOM и события
- CSS не содержит JS, JS не содержит CSS-строк

### 3. Обработка ошибок и граничных случаев
- Все недопустимые операции (деление на ноль, пустой ввод, некорректный тип) обрабатываются явно
- Пользователь получает понятное сообщение об ошибке, а не `NaN`, `undefined` или пустой экран
- Нет необработанных исключений, которые сломают UI

### 4. Стабильность layout
- Элементы с динамическим контентом имеют фиксированные или ограниченные размеры (`max-width`, `overflow: hidden`, `text-overflow: ellipsis`)
- Layout не ломается при длинных текстах, пустых списках или большом количестве элементов
- Используется `flex` или `grid` — никаких `float` и абсолютного позиционирования для основного layout

### 5. Корректность ссылок
- Все `href`, `src` пути в HTML указывают на существующие файлы с правильными относительными путями
- Все классы и id, используемые в JS, присутствуют в HTML
- Все `data-*` атрибуты, читаемые в JS, проставлены на нужных элементах в HTML

### 6. Хранение данных
- Если используется `localStorage` — данные сериализуются через `JSON.stringify` и парсятся через `JSON.parse`
- При загрузке страницы проверяется наличие данных в `localStorage` перед чтением

## Исходные файлы для проверки

{code}

## Формат вывода

Верни исправленные файлы в том же формате (все файлы, даже не изменённые):
{file_markers}
"""


def _parse_files(response: str) -> dict[str, str]:
    files: dict[str, str] = {}
    pattern = r"---FILE:\s*(.+?)---\n(.*?)(?=---FILE:|---README---|$)"
    for path, content in re.findall(pattern, response, re.DOTALL):
        content = re.sub(r"^```\w*\s*\n?", "", content.strip(), flags=re.IGNORECASE)
        content = re.sub(r"\n?```\s*$", "", content)
        files[path.strip()] = content.strip()

    readme_match = re.search(r"---README---\n(.*?)$", response, re.DOTALL)
    if readme_match:
        files["README.md"] = readme_match.group(1).strip()

    return files


def _files_to_text(files: dict[str, str]) -> str:
    parts = []
    for path, content in files.items():
        if path != "README.md":
            parts.append(f"---FILE: {path}---\n{content}")
    return "\n\n".join(parts)


def _build_file_markers(file_paths: list[str]) -> str:
    """Build the expected output format string for self-check prompt."""
    lines = []
    for p in file_paths:
        lines.append(f"---FILE: {p}---\n<содержимое>")
    return "\n".join(lines)


def _expected_files_from_plan(plan: dict) -> set[str]:
    """Extract expected file paths from the architecture plan."""
    if not plan or "files" not in plan:
        return set()
    return {f["path"] for f in plan.get("files", []) if isinstance(f, dict) and "path" in f}


def run(
    functional_req: str,
    non_functional_req: str,
    features: str,
    run_id: str,
    architecture_plan: str | dict = "",
) -> dict:
    print("[AgentCoder] starting...")

    plan_dict: dict = {}
    if isinstance(architecture_plan, dict):
        plan_dict = architecture_plan
        architecture_plan_str = json.dumps(architecture_plan, ensure_ascii=False, indent=2)
    else:
        architecture_plan_str = architecture_plan
        if architecture_plan_str:
            try:
                plan_dict = json.loads(architecture_plan_str)
            except json.JSONDecodeError:
                pass

    template = _jinja_env.get_template("coder.j2")
    user_prompt = template.render(
        functional_req=functional_req,
        non_functional_req=non_functional_req,
        features=features,
        architecture_plan=architecture_plan_str,
    )

    system_prompt = (
        "Ты опытный senior frontend-разработчик. "
        "Генерируй чистый, рабочий HTML/CSS/JS код разбитый на файлы. "
        "Строго соблюдай маркеры вывода ---FILE: path--- и ---README---. "
        "README пиши на русском языке."
    )

    response = call_llm(system=system_prompt, user=user_prompt, model=get_model("coder"))
    files = _parse_files(response)

    # Определяем ожидаемые файлы из плана (если он есть), иначе — что вернула модель
    expected = _expected_files_from_plan(plan_dict) or set(files.keys()) - {"README.md"}
    missing = expected - set(files.keys())
    if missing:
        print(f"[AgentCoder] WARNING: missing files after parse: {missing}")

    # Self-check: универсальная проверка качества
    print("[AgentCoder] running self-check pass...")
    try:
        src_files = {k: v for k, v in files.items() if k != "README.md"}
        src_paths = sorted(src_files.keys())
        fixed_response = call_llm(
            system=_SELF_CHECK_SYSTEM,
            user=_SELF_CHECK_PROMPT.format(
                code=_files_to_text(src_files),
                file_markers=_build_file_markers(src_paths),
            ),
            model=get_model("self_check"),
        )
        fixed_files = _parse_files(fixed_response)
        # Применяем только если вернулось не меньше файлов чем было
        returned = set(fixed_files.keys()) - {"README.md"}
        if returned >= set(src_files.keys()):
            for key in src_files:
                if key in fixed_files:
                    files[key] = fixed_files[key]
            print("[AgentCoder] self-check applied successfully")
        else:
            print(f"[AgentCoder] WARNING: self-check returned fewer files ({returned} vs {set(src_files.keys())}), keeping original")
    except Exception as e:
        print(f"[AgentCoder] WARNING: self-check failed ({e}), keeping original code")

    written: list[str] = []
    readme_content = files.pop("README.md", "# Приложение\n\nОткройте `src/index.html` в браузере.\n\n## Тесты\n\n```\npytest tests/\n```")
    for rel_path, content in files.items():
        write_artifact(run_id, f"src/{rel_path}", content)
        written.append(f"src/{rel_path}")

    write_artifact(run_id, "README.md", readme_content)

    print(f"[AgentCoder] done, wrote: {written + ['README.md']}")
    return {
        "src_files": written,
        "readme": "README.md",
    }


def fix(functional_req: str, test_output: str, run_id: str) -> None:
    """Read current src files, ask LLM to fix them based on failed test output, write back."""
    print("[AgentCoder:fix] reading current src files...")

    src_dir = os.path.join("output", run_id, "src")
    current_files: dict[str, str] = {}
    for dirpath, _, filenames in os.walk(src_dir):
        for fname in sorted(filenames):
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, src_dir)
            try:
                with open(full, encoding="utf-8") as f:
                    current_files[rel] = f.read()
            except Exception:
                pass

    if not current_files:
        print("[AgentCoder:fix] WARNING: no src files found, skipping fix")
        return

    src_paths = sorted(current_files.keys())
    src_text = _files_to_text(current_files)

    template = _jinja_env.get_template("fixer.j2")
    user_prompt = template.render(
        functional_req=functional_req,
        test_output=test_output,
        src_code=src_text,
        file_markers=_build_file_markers(src_paths),
    )

    system_prompt = (
        "Ты опытный senior разработчик. "
        "Исправляй только то что нужно для прохождения тестов. "
        "Строго соблюдай маркеры ---FILE: path---. "
        "Выводи ВСЕ файлы, даже неизменённые."
    )

    try:
        response = call_llm(system=system_prompt, user=user_prompt, model=get_model("fixer"))
        fixed = _parse_files(response)
        written = []
        for rel_path, content in fixed.items():
            if rel_path == "README.md":
                continue
            write_artifact(run_id, f"src/{rel_path}", content)
            written.append(rel_path)
        print(f"[AgentCoder:fix] fixed and wrote: {written}")
    except Exception as e:
        print(f"[AgentCoder:fix] WARNING: fix call failed ({e}), keeping original")


def patch(instruction: str, run_id: str) -> list[str]:
    """Apply a targeted instruction (e.g. 'change background color') to existing src files."""
    print(f"[AgentCoder:patch] instruction: {instruction!r}")

    src_dir = os.path.join("output", run_id, "src")
    current_files: dict[str, str] = {}
    for dirpath, _, filenames in os.walk(src_dir):
        for fname in sorted(filenames):
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, src_dir)
            try:
                with open(full, encoding="utf-8") as f:
                    current_files[rel] = f.read()
            except Exception:
                pass

    if not current_files:
        print("[AgentCoder:patch] WARNING: no src files found, skipping patch")
        return []

    src_paths = sorted(current_files.keys())

    template = _jinja_env.get_template("patcher.j2")
    user_prompt = template.render(
        instruction=instruction,
        src_code=_files_to_text(current_files),
        file_markers=_build_file_markers(src_paths),
    )

    system_prompt = (
        "Ты опытный senior frontend-разработчик. "
        "Вноси только минимально необходимые изменения по инструкции. "
        "Строго соблюдай маркеры ---FILE: path---. "
        "Выводи ТОЛЬКО изменённые файлы."
    )

    response = call_llm(system=system_prompt, user=user_prompt, model=get_model("patcher"))
    patched = _parse_files(response)

    written = []
    for rel_path, content in patched.items():
        if rel_path == "README.md":
            continue
        write_artifact(run_id, f"src/{rel_path}", content)
        written.append(rel_path)

    print(f"[AgentCoder:patch] patched files: {written}")
    return written
