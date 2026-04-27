import os
from jinja2 import Environment, FileSystemLoader
from utils.llm_client import call_llm
from utils.file_writer import write_artifact

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")
_jinja_env = Environment(loader=FileSystemLoader(_PROMPTS_DIR))


def run(bt: str, bp: str, features: str, run_id: str) -> dict:
    print("[AgentUseCases] starting...")

    template = _jinja_env.get_template("use_cases.j2")
    user_prompt = template.render(bt=bt, bp=bp, features=features)

    system_prompt = (
        "Ты опытный бизнес-аналитик программного обеспечения. "
        "Отвечай строго на русском языке. "
        "Выводи только содержимое файла use-cases.md без лишних пояснений."
    )

    use_cases = call_llm(system=system_prompt, user=user_prompt)

    write_artifact(run_id, "docs/use-cases.md", use_cases)
    print("[AgentUseCases] done, wrote: docs/use-cases.md")
    return {"use_cases": use_cases}
