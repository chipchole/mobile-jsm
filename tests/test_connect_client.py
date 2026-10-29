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


def test_token_refreshed_before_expiry():
    _, tokens, transport, clock = make(token_refresh_skew_seconds=120)
    tokens.get()
    clock.advance(3600 - 119)  # inside the skew window
    assert tokens.get() == "tok-2"
    assert transport.tokens_issued == 2


def test_401_invalidates_token_and_retries_once():
    client, _, transport, _ = make()
    client.start_outbound_callback(phone_number="+61755504100", queue_id="q", contact_flow_id="f")
    transport.expire_all_tokens()  # e.g. signing key rotated
    contact_id = client.start_outbound_callback(phone_number="+61755504100", queue_id="q", contact_flow_id="f")
    assert contact_id.startswith("contact-")
    assert transport.tokens_issued == 2


def test_repeated_401_raises_auth_error():
    client, _, transport, _ = make()

    class AlwaysRejects(set):
        def add(self, item):
            pass  # identity provider issues tokens Connect never accepts

    transport.valid_tokens = AlwaysRejects()
    with pytest.raises(AuthError):
        client.start_outbound_callback(phone_number="+61755504100", queue_id="q", contact_flow_id="f")
    assert transport.tokens_issued == 2


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
