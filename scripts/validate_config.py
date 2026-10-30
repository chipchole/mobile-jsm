"""Validate routing rules, queues and contact flows before deploy."""
import json
import pathlib
import sys

import yaml

root = pathlib.Path(__file__).resolve().parent.parent
errors = []

queues = yaml.safe_load((root / "config/queues.yaml").read_text())["queues"]
rules = yaml.safe_load((root / "config/routing_rules.yaml").read_text())["rules"]

for key, q in queues.items():
    if q.get("failover_queue") and q["failover_queue"] not in queues:
        errors.append(f"queue {key}: failover_queue {q['failover_queue']} does not exist")
for rule in rules:
    if rule["queue"] not in queues:
        errors.append(f"rule {rule['name']}: unknown queue {rule['queue']}")
if not rules or rules[-1].get("match"):
    errors.append("routing_rules.yaml must end with a default rule (no match block)")

for flow in (root / "contact-flows").glob("*.json"):
    data = json.loads(flow.read_text())
    ids = {a["Identifier"] for a in data["Actions"]}
    if data["StartAction"] not in ids:
        errors.append(f"{flow.name}: StartAction {data['StartAction']} not found")

numbers = yaml.safe_load((root / "config/numbers.yaml").read_text())["numbers"]
flows = {f.stem for f in (root / "contact-flows").glob("*.json")}
for n in numbers:
    if n["flow"] not in flows:
        errors.append(f"number {n['label']}: unknown flow {n['flow']}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: {len(queues)} queues, {len(rules)} rules, {len(flows)} flows, {len(numbers)} numbers")
