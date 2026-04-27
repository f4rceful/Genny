import os
import openai
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "qwen/qwen3-235b-a22b"
FALLBACK_MODEL = "qwen/qwen3-30b-a3b"

# Имена агентов → переменная окружения
_AGENT_ENV: dict[str, str] = {
    "use_cases":  "MODEL_USE_CASES",
    "analyst":    "MODEL_ANALYST",
    "architect":  "MODEL_ARCHITECT",
    "coder":      "MODEL_CODER",
    "self_check": "MODEL_CODER",   # self-check использует ту же модель что и coder
    "tester":     "MODEL_TESTER",
    "fixer":      "MODEL_FIXER",
    "patcher":    "MODEL_PATCHER",
}


def get_model(agent: str) -> str:
    """Return model for the given agent, reading from env vars with fallback chain:
    MODEL_<AGENT> → MODEL_DEFAULT → hardcoded DEFAULT_MODEL
    """
    env_key = _AGENT_ENV.get(agent, f"MODEL_{agent.upper()}")
    model = os.environ.get(env_key, "").strip()
    if not model:
        model = os.environ.get("MODEL_DEFAULT", "").strip()
    if not model:
        model = DEFAULT_MODEL
    return model


def _strip_thinking(text: str) -> str:
    idx = text.find("</think>")
    if idx != -1:
        return text[idx + len("</think>"):].lstrip("\n")
    return text


def call_llm(system: str, user: str, model: str = "") -> str:
    if not model:
        model = get_model("default")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is not set")

    fallback = os.environ.get("MODEL_FALLBACK", "").strip() or FALLBACK_MODEL

    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/generator-hackathon",
            "X-Title": "generator-hackathon",
        },
    )

    def _request(m: str) -> str:
        response = client.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""

    try:
        raw = _request(model)
    except Exception as e:
        print(f"[llm_client] Primary model {model!r} failed: {e}. Falling back to {fallback!r}")
        try:
            raw = _request(fallback)
        except Exception as e2:
            raise RuntimeError(f"Both models failed. Last error: {e2}") from e2

    return _strip_thinking(raw)
