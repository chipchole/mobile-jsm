"""Amazon Connect API client used by the callback service.

Authentication uses OAuth2 client credentials. The identity provider issues
access tokens with a 1 hour lifetime (`expires_in` = 3600). We cache the
token in memory for the life of the Lambda execution environment and
refresh it `token_refresh_skew_seconds` before it expires.

If Connect still returns 401 (for example the token was revoked, or the
signing key rotated), we invalidate the cached token and retry the request
once with a fresh token. See ITO-9851 / ITO-9849 for background.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Protocol

from . import retry
from .config import Settings
from .logging_utils import get_logger, log_event

log = get_logger("callback.connect")


class Transport(Protocol):
    def post(self, url: str, json: dict, headers: dict) -> "Response": ...


@dataclass
class Response:
    status: int
    body: dict


class AuthError(Exception):
    pass


class ConnectError(Exception):
    pass


@dataclass
class CachedToken:
    value: str
    expires_at: float


class TokenProvider:
    def __init__(self, settings: Settings, transport: Transport, clock: Callable[[], float] = time.time):
        self._settings = settings
        self._transport = transport
        self._clock = clock
        self._cached: CachedToken | None = None

    def get(self) -> str:
        now = self._clock()
        if self._cached and now < self._cached.expires_at - self._settings.token_refresh_skew_seconds:
            return self._cached.value
        return self._refresh(now)

    def invalidate(self) -> None:
        self._cached = None

    def _refresh(self, now: float) -> str:
        resp = self._transport.post(
            self._settings.auth_url,
            json={"grant_type": "client_credentials", "client_id": self._settings.client_id},
            headers={},
        )
        if resp.status != 200:
            raise AuthError(f"token endpoint returned {resp.status}")
        token = resp.body["access_token"]
        expires_in = int(resp.body.get("expires_in", 3600))
        self._cached = CachedToken(value=token, expires_at=now + expires_in)
        log_event(log, "token_refreshed", expires_in=expires_in)
        return token


class ConnectClient:
    def __init__(self, settings: Settings, transport: Transport, tokens: TokenProvider,
                 sleep: Callable[[float], None] = time.sleep):
        self._s = settings
        self._t = transport
        self._tokens = tokens
        self._sleep = sleep

    def start_outbound_callback(self, *, phone_number: str, queue_id: str, contact_flow_id: str,
                                attributes: dict | None = None) -> str:
        """Schedule an outbound callback and return the Connect ContactId."""
        payload = {
            "InstanceId": self._s.connect_instance_id,
            "DestinationPhoneNumber": phone_number,
            "QueueId": queue_id,
            "ContactFlowId": contact_flow_id,
            "Attributes": attributes or {},
        }

        def attempt() -> str:
            resp = self._post_authorised("/contact/outbound-voice", payload)
            if resp.status == 429:
                raise retry.ThrottlingError("Connect throttled StartOutboundVoiceContact")
            if resp.status >= 500:
                raise retry.TransientError(f"Connect returned {resp.status}")
            if resp.status != 200:
                raise ConnectError(f"Connect returned {resp.status}: {resp.body}")
            return resp.body["ContactId"]

        return retry.call_with_retry(
            attempt,
            attempts=self._s.retry_max_attempts,
            base_delay=self._s.retry_base_delay_seconds,
            max_delay=self._s.retry_max_delay_seconds,
            sleep=self._sleep,
        )

    def _post_authorised(self, path: str, payload: dict) -> Response:
        url = self._s.connect_api_url + path
        resp = self._t.post(url, json=payload, headers={"Authorization": f"Bearer {self._tokens.get()}"})
        if resp.status == 401:
            # Token rejected: drop it and retry exactly once with a new one.
            log_event(log, "token_rejected_retrying", path=path)
            self._tokens.invalidate()
            resp = self._t.post(url, json=payload, headers={"Authorization": f"Bearer {self._tokens.get()}"})
            if resp.status == 401:
                raise AuthError("Connect rejected a freshly issued token")
        return resp
