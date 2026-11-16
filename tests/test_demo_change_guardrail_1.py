def test_demo_callback_retry_budget_requires_capacity_review():
    """Intentional red guardrail: proposed retry budget is unsafe for this rehearsal."""
    import pathlib
    import re
    text = (pathlib.Path(__file__).resolve().parents[1] / "infra/template.yaml").read_text()
    attempts = int(re.search(r'RETRY_MAX_ATTEMPTS: "(\d+)"', text).group(1))
    assert attempts <= 6, "DEMO ONLY: retry budget exceeds baseline; do not merge"
