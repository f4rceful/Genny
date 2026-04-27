import os
import re
from jinja2 import Environment, FileSystemLoader
from utils.llm_client import call_llm
from utils.file_writer import write_artifact

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")
_jinja_env = Environment(loader=FileSystemLoader(_PROMPTS_DIR))


def _strip_code_fences(text: str) -> str:
    """Remove ```html ... ``` or ``` ... ``` wrappers if present."""
    text = text.strip()
    text = re.sub(r"^```(?:html)?\s*\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def run(functional_req: str, non_functional_req: str, features: str, run_id: str) -> dict:
    print("[AgentCoder] starting...")

    template = _jinja_env.get_template("coder.j2")
    user_prompt = template.render(
        functional_req=functional_req,
        non_functional_req=non_functional_req,
        features=features,
    )

    system_prompt = (
        "Ты опытный senior frontend-разработчик. "
        "Генерируй чистый, рабочий HTML/CSS/JS код. "
        "Отвечай строго по структуре из задания. "
        "README пиши на русском языке."
    )

    response = call_llm(system=system_prompt, user=user_prompt)

    parts = response.split("---README---", maxsplit=1)
    if len(parts) == 2:
        raw_html = parts[0].strip()
        readme_content = parts[1].strip()
    else:
        print("[AgentCoder] WARNING: ---README--- marker not found, using full response as HTML")
        raw_html = response.strip()
        readme_content = "# Приложение\n\nОткройте файл `src/index.html` в любом современном браузере."

    html_content = _strip_code_fences(raw_html)

    write_artifact(run_id, "src/index.html", html_content)
    write_artifact(run_id, "README.md", readme_content)

    print(f"[AgentCoder] done, wrote: src/index.html, README.md")
    return {
        "src_files": ["src/index.html"],
        "readme": "README.md",
    }
