"""Offline demo guardrail: never calls AWS or sends traffic."""
from pathlib import Path
import re

def test_demo_callback_capacity_budget():
    text = (Path(__file__).resolve().parents[1] / "infra/template.yaml").read_text()
    concurrency = int(re.search(r"ReservedConcurrentExecutions: (\d+)", text).group(1))
    attempts = int(re.search(r'RETRY_MAX_ATTEMPTS: "(\d+)"', text).group(1))
    assert concurrency <= 150, "Demo capacity budget exceeded"
    assert attempts <= 6, "Demo retry budget exceeded"
