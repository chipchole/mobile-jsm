from datetime import datetime, timezone

import pytest

from services.callback.queue_router import QueueRouter

# 10:00 Brisbane time (UTC+10)
OPEN = datetime(2026, 10, 29, 0, 0, tzinfo=timezone.utc)
# 22:30 Brisbane time
LATE = datetime(2026, 10, 29, 12, 30, tzinfo=timezone.utc)


@pytest.fixture
def router():
    return QueueRouter.from_files("config/queues.yaml", "config/routing_rules.yaml")


def test_priority_segment_goes_to_priority_queue(router):
    d = router.route(segment="priority", reason="general", at=OPEN, current_wait={})
    assert d.queue.key == "priority" and not d.failed_over


def test_segment_match_is_case_insensitive(router):
    # Regression test for ITO-9837
    d = router.route(segment="Priority", reason="general", at=OPEN, current_wait={})
    assert d.queue.key == "priority"


def test_priority_fails_over_when_wait_too_long(router):
    d = router.route(segment="priority", reason="general", at=OPEN, current_wait={"priority": 600})
    assert d.queue.key == "general" and d.failed_over


def test_after_hours_failover(router):
    d = router.route(segment="standard", reason="general", at=LATE, current_wait={})
    assert d.queue.key == "after_hours"


def test_default_rule(router):
    d = router.route(segment="standard", reason="something-else", at=OPEN, current_wait={})
    assert d.rule == "default"


def test_campaign_calls_go_to_overflow(router):
    d = router.route(segment="standard", reason="campaign", at=OPEN, current_wait={})
    assert d.queue.key == "overflow"


def test_general_fails_over_to_overflow_when_busy(router):
    d = router.route(segment="standard", reason="general", at=OPEN, current_wait={"general": 1200})
    assert d.queue.key == "overflow" and d.failed_over
