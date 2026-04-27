import os
from jinja2 import Environment, FileSystemLoader
from utils.llm_client import call_llm
from utils.file_writer import write_artifact

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")
_jinja_env = Environment(loader=FileSystemLoader(_PROMPTS_DIR))


def run(bt: str, bp: str, features: str, run_id: str) -> dict:
    print("[AgentAnalyst] starting...")

    template = _jinja_env.get_template("analyst.j2")
    user_prompt = template.render(bt=bt, bp=bp, features=features)

    system_prompt = (
        "Ты опытный бизнес-аналитик программного обеспечения. "
        "Отвечай строго на русском языке. "
        "Соблюдай структуру и маркеры, указанные в задании."
    )

    response = call_llm(system=system_prompt, user=user_prompt)

    parts = response.split("---SPLIT---", maxsplit=1)
    if len(parts) == 2:
        non_functional_req = parts[0].strip()
        functional_req = parts[1].strip()
    else:
        # Fallback: если модель не вставила маркер, считаем весь текст НФТ
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
