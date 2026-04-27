from pipeline import agent_analyst, agent_coder


def run_pipeline(bt: str, bp: str, features: str, run_id: str) -> list[str]:
    print(f"[Runner] starting pipeline for run_id={run_id}")

    analyst_result = agent_analyst.run(bt=bt, bp=bp, features=features, run_id=run_id)
    coder_result = agent_coder.run(
        functional_req=analyst_result["functional_req"],
        non_functional_req=analyst_result["non_functional_req"],
        features=features,
        run_id=run_id,
    )

    artifacts = [
        "docs/non-functional-req.md",
        "docs/functional-req.md",
        *coder_result["src_files"],
        coder_result["readme"],
    ]

    print(f"[Runner] pipeline complete. Artifacts: {artifacts}")
    return artifacts
