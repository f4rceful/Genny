from pipeline import agent_use_cases, agent_analyst, agent_architect, agent_coder, agent_tester


def run_pipeline(bt: str, bp: str, features: str, run_id: str) -> list[str]:
    print(f"[Runner] starting pipeline for run_id={run_id}")

    # Шаг 1: Use-cases
    agent_use_cases.run(bt=bt, bp=bp, features=features, run_id=run_id)

    # Шаг 2: НФТ + ФТ
    analyst_result = agent_analyst.run(bt=bt, bp=bp, features=features, run_id=run_id)

    # Шаг 3: Архитектурный план (файлы, классы, зависимости)
    architect_result = agent_architect.run(
        functional_req=analyst_result["functional_req"],
        non_functional_req=analyst_result["non_functional_req"],
        features=features,
        run_id=run_id,
    )

    # Шаг 4: Код по плану (с self-check внутри)
    coder_result = agent_coder.run(
        functional_req=analyst_result["functional_req"],
        non_functional_req=analyst_result["non_functional_req"],
        features=features,
        run_id=run_id,
        architecture_plan=architect_result["plan"],
    )

    # Шаг 5: Тесты
    tester_result = agent_tester.run(
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

    print(f"[Runner] pipeline complete. Artifacts: {artifacts}")
    return artifacts
