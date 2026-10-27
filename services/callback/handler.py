"""Lambda entry point: schedule a customer callback.

Invoked by the "Callback offer" contact flow (contact-flows/callback-offer.json)
and by the mobile app's "Call me back" button via API Gateway.
"""
from __future__ import annotations

import json
import logging
import urllib.request
from datetime import datetime, timezone

from . import config, phone
from .connect_client import AuthError, ConnectClient, Response, TokenProvider
from .logging_utils import get_logger, log_event
from .queue_router import QueueRouter
from .retry import RetryableError

log = get_logger("callback.handler")

CALLBACK_FLOW_ID = "callback-outbound-v3"


class UrllibTransport:
    def post(self, url: str, json: dict, headers: dict) -> Response:  # noqa: A002 - mirrors requests API
        data = __import__("json").dumps(json).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return Response(r.status, __import__("json").loads(r.read() or b"{}"))
        except urllib.error.HTTPError as e:
            return Response(e.code, {"error": e.reason})


_settings = config.load()
_transport = UrllibTransport()
_tokens = TokenProvider(_settings, _transport)
_client = ConnectClient(_settings, _transport, _tokens)
_router: QueueRouter | None = None


def _get_router() -> QueueRouter:
    global _router
    if _router is None:
        _router = QueueRouter.from_files(_settings.queues_path, _settings.routing_rules_path)
    return _router


def handle(event: dict, client: ConnectClient | None = None, router: QueueRouter | None = None,
           now: datetime | None = None) -> dict:
    client = client or _client
    router = router or _get_router()
    now = now or datetime.now(timezone.utc)

    body = event.get("body")
    request = json.loads(body) if isinstance(body, str) else (body or event)

    try:
        number = phone.normalise(request["phone_number"])
    except (KeyError, phone.InvalidPhoneNumber) as exc:
        log_event(log, "callback_rejected", logging.WARNING, reason=str(exc))
        return {"statusCode": 400, "body": json.dumps({"error": "invalid phone number"})}

    decision = router.route(
        segment=request.get("segment", "standard"),
        reason=request.get("reason", "general"),
        at=now,
        current_wait=request.get("current_wait", {}),
    )

    try:
        contact_id = client.start_outbound_callback(
            phone_number=number,
            queue_id=decision.queue.queue_id,
            contact_flow_id=CALLBACK_FLOW_ID,
            attributes={"segment": request.get("segment", "standard"), "rule": decision.rule},
        )
    except AuthError:
        log_event(log, "callback_failed_auth", logging.ERROR, queue=decision.queue.key, phone_number=number)
        return {"statusCode": 502, "body": json.dumps({"error": "contact centre authentication failed"})}
    except RetryableError:
        log_event(log, "callback_failed_throttled", logging.ERROR, queue=decision.queue.key, phone_number=number)
        return {"statusCode": 503, "body": json.dumps({"error": "contact centre busy, try again"})}

    log_event(log, "callback_scheduled", queue=decision.queue.key, rule=decision.rule,
              failed_over=decision.failed_over, contact_id=contact_id, phone_number=number)
    return {"statusCode": 202, "body": json.dumps({"contact_id": contact_id, "queue": decision.queue.key})}


def lambda_handler(event, context):  # pragma: no cover - thin AWS wrapper
    return handle(event)
