import json
from datetime import datetime, timezone

from services.callback import handler
from services.callback.config import Settings
from services.callback.connect_client import ConnectClient, TokenProvider
from services.callback.queue_router import QueueRouter
from tests.fakes import FakeClock, FakeTransport

OPEN = datetime(2026, 10, 29, 0, 0, tzinfo=timezone.utc)


def make_client():
    s = Settings()
    t = FakeTransport()
    return ConnectClient(s, t, TokenProvider(s, t, clock=FakeClock()), sleep=lambda x: None), t


def router():
    return QueueRouter.from_files("config/queues.yaml", "config/routing_rules.yaml")


def test_schedules_callback():
    client, _ = make_client()
    resp = handler.handle({"body": json.dumps({"phone_number": "0491 570 006", "segment": "priority"})},
                          client=client, router=router(), now=OPEN)
    assert resp["statusCode"] == 202
    assert json.loads(resp["body"])["queue"] == "priority"


def test_invalid_number_is_rejected():
    client, _ = make_client()
    resp = handler.handle({"phone_number": "12"}, client=client, router=router(), now=OPEN)
    assert resp["statusCode"] == 400


def test_logs_do_not_contain_raw_number(capsys):
    client, _ = make_client()
    handler.handle({"phone_number": "0491 570 006"}, client=client, router=router(), now=OPEN)
    out = capsys.readouterr().out
    assert "491570006" not in out
