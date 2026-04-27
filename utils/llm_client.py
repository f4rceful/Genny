import os
import re
import openai
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "qwen/qwen3-235b-a22b"
FALLBACK_MODEL = "qwen/qwen3-30b-a3b"


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks that Qwen3 models may emit."""
    idx = text.find("</think>")
    if idx != -1:
        return text[idx + len("</think>"):].lstrip("\n")
    return text


def call_llm(system: str, user: str, model: str = DEFAULT_MODEL) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is not set")

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
        print(f"[llm_client] Primary model {model!r} failed: {e}. Falling back to {FALLBACK_MODEL!r}")
        try:
            raw = _request(FALLBACK_MODEL)
        except Exception as e2:
            raise RuntimeError(f"Both models failed. Last error: {e2}") from e2

    return _strip_thinking(raw)
