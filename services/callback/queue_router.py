"""Chooses the Amazon Connect queue for a callback.

Rules live in config/routing_rules.yaml so the contact centre team can
change routing without a code change. Rules are evaluated top to bottom;
the first match wins. If the chosen queue is unavailable (closed, or over
its max_wait_seconds) we fail over to the queue's `failover_queue`.

ITO-9837: priority customers were routed to the general queue after a
routing-rule release because the segment match was case-sensitive. Segment
matching is now case-insensitive and covered by tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import yaml


@dataclass(frozen=True)
class Queue:
    key: str
    queue_id: str
    hours: tuple[int, int]
    max_wait_seconds: int
    failover_queue: str | None
    timezone: str = "Australia/Brisbane"

    def is_open(self, at: datetime) -> bool:
        local = at.astimezone(ZoneInfo(self.timezone))
        start, end = self.hours
        return start <= local.hour < end


@dataclass(frozen=True)
class RoutingDecision:
    queue: Queue
    rule: str
    failed_over: bool = False


class QueueRouter:
    def __init__(self, queues: dict[str, Queue], rules: list[dict]):
        self.queues = queues
        self.rules = rules

    @classmethod
    def from_files(cls, queues_path: str, rules_path: str) -> "QueueRouter":
        with open(queues_path) as fh:
            raw_queues = yaml.safe_load(fh)["queues"]
        with open(rules_path) as fh:
            rules = yaml.safe_load(fh)["rules"]
        queues = {
            key: Queue(
                key=key,
                queue_id=q["queue_id"],
                hours=tuple(q["hours"]),
                max_wait_seconds=q["max_wait_seconds"],
                failover_queue=q.get("failover_queue"),
                timezone=q.get("timezone", "Australia/Brisbane"),
            )
            for key, q in raw_queues.items()
        }
        return cls(queues, rules)

    def route(self, *, segment: str, reason: str, at: datetime, current_wait: dict[str, int]) -> RoutingDecision:
        for rule in self.rules:
            match = rule.get("match", {})
            if match.get("segment") not in (None, segment):
                continue
            if match.get("reason") not in (None, reason):
                continue
            return self._with_failover(self.queues[rule["queue"]], rule["name"], at, current_wait)
        raise LookupError("no routing rule matched; routing_rules.yaml must end with a default rule")

    def _with_failover(self, queue: Queue, rule: str, at: datetime, current_wait: dict[str, int]) -> RoutingDecision:
        seen = set()
        failed_over = False
        while queue.key not in seen:
            seen.add(queue.key)
            healthy = queue.is_open(at) and current_wait.get(queue.key, 0) <= queue.max_wait_seconds
            if healthy or not queue.failover_queue:
                return RoutingDecision(queue=queue, rule=rule, failed_over=failed_over)
            queue = self.queues[queue.failover_queue]
            failed_over = True
        raise RuntimeError(f"failover loop detected starting at rule {rule}")
