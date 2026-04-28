"""Оркестратор пайплайна: запускает агентов по цепочке и управляет циклом автоисправления тестов."""
import os

from pipeline import agent_use_cases, agent_analyst, agent_architect, agent_coder, agent_tester
from utils import state, cancel as cancel_utils
from utils.cancel import CancelledError
from utils.llm_client import get_model
from utils.test_runner import run_tests

MAX_FIX_ATTEMPTS = int(os.environ.get("MAX_FIX_ATTEMPTS", 3))


def _check_cancel(run_id: str) -> None:
    """Проверяет флаг отмены между шагами пайплайна и бросает CancelledError если он установлен."""
    if cancel_utils.is_cancelled(run_id):
        raise CancelledError("Отменено пользователем")


def run_pipeline(bt: str, bp: str, features: str, run_id: str) -> list[str]:
    """Запускает полный пайплайн генерации: юз-кейсы → аналитик → архитектор → кодер → тестер → цикл исправлений.

    Возвращает список путей всех сгенерированных артефактов.
    """
    print(f"[Runner] starting pipeline for run_id={run_id}")
    state.write(run_id, "running", step="initializing")

    try:
        _check_cancel(run_id)
        state.write(run_id, "running", step="use-cases", model=get_model("use_cases"))
        use_cases_result = agent_use_cases.run(bt=bt, bp=bp, features=features, run_id=run_id)

        _check_cancel(run_id)
        state.write(run_id, "running", step="analyst", model=get_model("analyst"))
        analyst_result = agent_analyst.run(
            bt=bt, bp=bp, features=features, run_id=run_id,
            use_cases=use_cases_result.get("use_cases", ""),
        )

        _check_cancel(run_id)
        state.write(run_id, "running", step="architect", model=get_model("architect"))
        architect_result = agent_architect.run(
            functional_req=analyst_result["functional_req"],
            non_functional_req=analyst_result["non_functional_req"],
            features=features,
            run_id=run_id,
        )

        _check_cancel(run_id)
        state.write(run_id, "running", step="coder", model=get_model("coder"))
        coder_result = agent_coder.run(
            functional_req=analyst_result["functional_req"],
            non_functional_req=analyst_result["non_functional_req"],
            features=features,
            run_id=run_id,
            architecture_plan=architect_result["plan"],
        )

        _check_cancel(run_id)
        state.write(run_id, "running", step="tester", model=get_model("tester"))
        tester_result = agent_tester.run(
            functional_req=analyst_result["functional_req"],
            run_id=run_id,
        )

        # Цикл автоисправления: запускаем тесты → если падают → исправляем код → повторяем
        for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
            _check_cancel(run_id)
            state.write(run_id, "running", step=f"test-check (попытка {attempt}/{MAX_FIX_ATTEMPTS})")
            print(f"[Runner] running tests (attempt {attempt}/{MAX_FIX_ATTEMPTS})...")
            result = run_tests(run_id)

            if result["passed"]:
                print(f"[Runner] all tests passed on attempt {attempt}")
                break

            print(f"[Runner] tests failed (attempt {attempt}):\n{result['output']}")

            if attempt == MAX_FIX_ATTEMPTS:
                print("[Runner] max fix attempts reached, proceeding with current code")
                break

            _check_cancel(run_id)
            state.write(run_id, "running", step=f"fixing (попытка {attempt}/{MAX_FIX_ATTEMPTS})", model=get_model("fixer"))
            agent_coder.fix(
                functional_req=analyst_result["functional_req"],
                test_output=result["output"],
                run_id=run_id,
            )

            # После исправления кода перегенерируем тесты — они тоже могут содержать ошибки
            _check_cancel(run_id)
            state.write(run_id, "running", step=f"re-testing (попытка {attempt}/{MAX_FIX_ATTEMPTS})", model=get_model("tester"))
            agent_tester.run(
                functional_req=analyst_result["functional_req"],
                run_id=run_id,
            )

        artifacts = [
            "docs/use-cases.md",
            "docs/non-functional-req.md",
            "docs/functional-req.md",
            "docs/architecture.json",
            *coder_result["src_files"],
            coder_result["readme"],
            tester_result["test_file"],
        ]

        state.write(run_id, "done", step="")
        print(f"[Runner] pipeline complete. Artifacts: {artifacts}")
        return artifacts

    except CancelledError:
        state.write(run_id, "cancelled", step="", error="Генерация отменена пользователем")
        print(f"[Runner] pipeline CANCELLED for run_id={run_id}")
        raise

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        current = state.read(run_id)
        state.write(run_id, "failed", step=current.get("step", ""), error=error_msg)
        print(f"[Runner] pipeline FAILED at step '{current.get('step')}': {error_msg}")
        raise

    finally:
        # Очищаем событие отмены в любом случае — успех, ошибка или отмена
        cancel_utils.cleanup(run_id)


def refine_pipeline(run_id: str) -> None:
    """Перезапускает цикл тестирования и исправления для уже сгенерированного проекта."""
    print(f"[Runner] starting refine for run_id={run_id}")

    fr_path = os.path.join("output", run_id, "docs", "functional-req.md")
    try:
        with open(fr_path, encoding="utf-8") as f:
            functional_req = f.read()
    except FileNotFoundError:
        raise RuntimeError(f"functional-req.md not found for run_id={run_id}")

    state.write(run_id, "running", step="refine: запуск тестов")

    try:
        for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
            _check_cancel(run_id)
            state.write(run_id, "running", step=f"refine: тест (попытка {attempt}/{MAX_FIX_ATTEMPTS})")
            print(f"[Runner:refine] running tests (attempt {attempt}/{MAX_FIX_ATTEMPTS})...")
            result = run_tests(run_id)

            if result["passed"]:
                print(f"[Runner:refine] all tests passed on attempt {attempt}")
                break

            print(f"[Runner:refine] tests failed (attempt {attempt}):\n{result['output']}")

            if attempt == MAX_FIX_ATTEMPTS:
                print("[Runner:refine] max fix attempts reached")
                break

            _check_cancel(run_id)
            state.write(run_id, "running", step=f"refine: исправление (попытка {attempt}/{MAX_FIX_ATTEMPTS})", model=get_model("fixer"))
            agent_coder.fix(
                functional_req=functional_req,
                test_output=result["output"],
                run_id=run_id,
            )

            _check_cancel(run_id)
            state.write(run_id, "running", step=f"refine: тесты (попытка {attempt}/{MAX_FIX_ATTEMPTS})", model=get_model("tester"))
            agent_tester.run(functional_req=functional_req, run_id=run_id)

        state.write(run_id, "done", step="")
        print(f"[Runner:refine] done for run_id={run_id}")

    except CancelledError:
        state.write(run_id, "cancelled", step="", error="Генерация отменена пользователем")
        print(f"[Runner:refine] CANCELLED for run_id={run_id}")
        raise

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        current = state.read(run_id)
        state.write(run_id, "failed", step=current.get("step", ""), error=error_msg)
        print(f"[Runner:refine] FAILED: {error_msg}")
        raise

    finally:
        cancel_utils.cleanup(run_id)
