def test_demo_failover_configuration_has_no_cycles():
    """Intentional red guardrail: the demo proposal introduces a cycle."""
    import pathlib
    import yaml
    root = pathlib.Path(__file__).resolve().parents[1]
    queues = yaml.safe_load((root / "config/queues.yaml").read_text())["queues"]
    for start in queues:
        seen = set()
        current = start
        while current:
            assert current not in seen, "DEMO ONLY: queue failover cycle; do not merge"
            seen.add(current)
            current = queues[current].get("failover_queue")
