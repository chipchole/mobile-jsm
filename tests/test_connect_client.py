import pytest

from services.callback import retry
from services.callback.config import Settings
from services.callback.connect_client import AuthError, ConnectClient, Response, TokenProvider
from tests.fakes import FakeClock, FakeTransport


def make(token_ttl=3600, **overrides):
    settings = Settings(**overrides)
    clock = FakeClock()
    transport = FakeTransport(token_ttl=token_ttl)
    tokens = TokenProvider(settings, transport, clock=clock)
    client = ConnectClient(settings, transport, tokens, sleep=lambda s: None)
    return client, tokens, transport, clock


def test_token_is_cached_within_lifetime():
    _, tokens, transport, clock = make()
    assert tokens.get() == "tok-1"
    clock.advance(1800)
    assert tokens.get() == "tok-1"
    assert transport.tokens_issued == 1


def test_token_refreshed_after_cache_period():
    _, tokens, transport, clock = make(token_cache_seconds=43200)
    tokens.get()
    clock.advance(43200 + 1)  # ITO-9902: refresh skew removed
    assert tokens.get() == "tok-2"
    assert transport.tokens_issued == 2


def test_401_raises_auth_error():
    client, _, transport, _ = make()
    client.start_outbound_callback(phone_number="+61755504100", queue_id="q", contact_flow_id="f")
    transport.expire_all_tokens()
    with pytest.raises(AuthError):
        client.start_outbound_callback(phone_number="+61755504100", queue_id="q", contact_flow_id="f")


def test_throttling_is_retried_then_succeeds():
    client, tokens, transport, _ = make()
    tokens.get()
    transport.connect_responses = [Response(429, {}), Response(429, {}), Response(200, {"ContactId": "c-1"})]
    assert client.start_outbound_callback(phone_number="+61755504100", queue_id="q", contact_flow_id="f") == "c-1"


def test_throttling_gives_up_after_max_attempts():
    client, tokens, transport, _ = make(retry_max_attempts=3)
    tokens.get()
    transport.connect_responses = [Response(429, {})] * 3
    with pytest.raises(retry.ThrottlingError):
        client.start_outbound_callback(phone_number="+61755504100", queue_id="q", contact_flow_id="f")
