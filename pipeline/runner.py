import os

from pipeline import agent_use_cases, agent_analyst, agent_architect, agent_coder, agent_tester
from utils import state
from utils.test_runner import run_tests

MAX_FIX_ATTEMPTS = int(os.environ.get("MAX_FIX_ATTEMPTS", 3))


def run_pipeline(bt: str, bp: str, features: str, run_id: str) -> list[str]:
    print(f"[Runner] starting pipeline for run_id={run_id}")
    state.write(run_id, "running", step="initializing")

    try:
        state.write(run_id, "running", step="use-cases")
        agent_use_cases.run(bt=bt, bp=bp, features=features, run_id=run_id)

        state.write(run_id, "running", step="analyst")
        analyst_result = agent_analyst.run(bt=bt, bp=bp, features=features, run_id=run_id)

        state.write(run_id, "running", step="architect")
        architect_result = agent_architect.run(
            functional_req=analyst_result["functional_req"],
            non_functional_req=analyst_result["non_functional_req"],
            features=features,
            run_id=run_id,
        )

        state.write(run_id, "running", step="coder")
        coder_result = agent_coder.run(
            functional_req=analyst_result["functional_req"],
            non_functional_req=analyst_result["non_functional_req"],
            features=features,
            run_id=run_id,
            architecture_plan=architect_result["plan"],
        )

        state.write(run_id, "running", step="tester")
        tester_result = agent_tester.run(
            functional_req=analyst_result["functional_req"],
            run_id=run_id,
        )

        # Цикл самопроверки: запускаем тесты и исправляем код пока они не пройдут
        for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
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

            state.write(run_id, "running", step=f"fixing (попытка {attempt}/{MAX_FIX_ATTEMPTS})")
            agent_coder.fix(
                functional_req=analyst_result["functional_req"],
                test_output=result["output"],
                run_id=run_id,
            )

            # Перегенерируем тесты под исправленный код
            state.write(run_id, "running", step=f"re-testing (попытка {attempt}/{MAX_FIX_ATTEMPTS})")
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

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        current = state.read(run_id)
        state.write(run_id, "failed", step=current.get("step", ""), error=error_msg)
        print(f"[Runner] pipeline FAILED at step '{current.get('step')}': {error_msg}")
        raise


def refine_pipeline(run_id: str) -> None:
    """Re-run fix loop on an existing run: test → fix → retest (up to MAX_FIX_ATTEMPTS)."""
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

            state.write(run_id, "running", step=f"refine: исправление (попытка {attempt}/{MAX_FIX_ATTEMPTS})")
            agent_coder.fix(
                functional_req=functional_req,
                test_output=result["output"],
                run_id=run_id,
            )

            state.write(run_id, "running", step=f"refine: тесты (попытка {attempt}/{MAX_FIX_ATTEMPTS})")
            agent_tester.run(functional_req=functional_req, run_id=run_id)

        state.write(run_id, "done", step="")
        print(f"[Runner:refine] done for run_id={run_id}")

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        current = state.read(run_id)
        state.write(run_id, "failed", step=current.get("step", ""), error=error_msg)
        print(f"[Runner:refine] FAILED: {error_msg}")
        raise
