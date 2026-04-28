"""LLM-клиент: отправка запросов через OpenRouter с поддержкой фолбэка и отмены генерации."""
import os
import time
import concurrent.futures
import openai
from dotenv import load_dotenv
from utils.cancel import is_cancelled, CancelledError

load_dotenv()

DEFAULT_MODEL = "google/gemini-3-flash-preview"
FALLBACK_MODEL = "deepseek/deepseek-v4-flash"

# Маппинг агентов → переменная окружения для независимой настройки модели каждого агента
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
    """Возвращает модель для агента: env-переменная агента → MODEL_DEFAULT → хардкод."""
    env_key = _AGENT_ENV.get(agent, f"MODEL_{agent.upper()}")
    model = os.environ.get(env_key, "").strip()
    if not model:
        model = os.environ.get("MODEL_DEFAULT", "").strip()
    if not model:
        model = DEFAULT_MODEL
    return model


def _strip_thinking(text: str) -> str:
    """Удаляет блок <think>...</think> из ответов моделей с цепочкой рассуждений (CoT)."""
    idx = text.find("</think>")
    if idx != -1:
        return text[idx + len("</think>"):].lstrip("\n")
    return text


def _run_with_cancel(fn, run_id: str):
    """Запускает fn в отдельном потоке и прерывает его при отмене запуска."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn)
        while not future.done():
            if is_cancelled(run_id):
                raise CancelledError("Отменено пользователем")
            time.sleep(0.5)
        return future.result()


def call_llm(system: str, user: str, model: str = "", run_id: str = "") -> str:
    """Отправляет запрос к LLM; при сбое основной модели переключается на фолбэк."""
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
            # Опциональные заголовки для идентификации в дашборде OpenRouter
            "HTTP-Referer": "https://github.com/f4rceful/Genny",
            "X-Title": "Genny",
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

    def _call(m: str) -> str:
        if run_id:
            return _run_with_cancel(lambda: _request(m), run_id)
        return _request(m)

    try:
        raw = _call(model)
    except CancelledError:
        raise
    except Exception as e:
        print(f"[llm_client] Primary model {model!r} failed: {e}. Falling back to {fallback!r}")
        try:
            raw = _call(fallback)
        except CancelledError:
            raise
        except Exception as e2:
            raise RuntimeError(f"Both models failed. Last error: {e2}") from e2

    return _strip_thinking(raw)
