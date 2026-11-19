"""Offline demo guardrail for queue failover cycles."""
from pathlib import Path
import yaml

def test_queue_failover_has_no_cycle():
    queues = yaml.safe_load((Path(__file__).resolve().parents[1] / "config/queues.yaml").read_text())["queues"]
    for origin in queues:
        seen = set()
        current = origin
        while current is not None:
            assert current not in seen, f"Failover cycle reachable from {origin}: {current}"
            seen.add(current)
            assert current in queues, f"Unknown failover queue: {current}"
            current = queues[current].get("failover_queue")
