import json
import os
import re
from jinja2 import Environment, FileSystemLoader
from utils.llm_client import call_llm
from utils.file_writer import write_artifact

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")
_jinja_env = Environment(loader=FileSystemLoader(_PROMPTS_DIR))


def _extract_json(text: str) -> str:
    """Strip markdown fences and extract the first JSON object from text."""
    text = re.sub(r"^```(?:json)?\s*\n?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\n?```\s*$", "", text)
    # Find the outermost JSON object in case of leading/trailing text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text


def run(functional_req: str, non_functional_req: str, features: str, run_id: str) -> dict:
    print("[AgentArchitect] starting...")

    template = _jinja_env.get_template("architect.j2")
    user_prompt = template.render(
        functional_req=functional_req,
        non_functional_req=non_functional_req,
        features=features,
    )

    system_prompt = (
        "Ты опытный software architect. "
        "Возвращай ТОЛЬКО валидный JSON без пояснений и без markdown-блоков. "
        "Никакого текста до или после JSON."
    )

    response = call_llm(system=system_prompt, user=user_prompt)
    raw_json = _extract_json(response)

    try:
        plan = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"[AgentArchitect] WARNING: failed to parse JSON ({e}), using raw text as plan")
        plan = {"raw": raw_json}

    # Сохраняем план как docs/architecture.json
    write_artifact(run_id, "docs/architecture.json", json.dumps(plan, ensure_ascii=False, indent=2))
    print("[AgentArchitect] done, wrote: docs/architecture.json")
    return {"plan": plan}
