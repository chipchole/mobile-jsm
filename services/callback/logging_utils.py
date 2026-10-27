"""Structured JSON logging with PII masking.

Our Logging and Customer Data Standard requires that customer phone
numbers, names and email addresses never appear in logs unmasked. The
`log_event` helper masks known PII fields automatically; do not bypass it
with print() or f-strings containing customer data.
"""
from __future__ import annotations

import json
import logging
import sys
import time

from . import phone

PII_PHONE_FIELDS = {"phone", "phone_number", "customer_number", "callback_number"}
PII_REDACT_FIELDS = {"customer_name", "email", "first_name", "last_name"}


def get_logger(name: str = "callback") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def scrub(fields: dict) -> dict:
    clean = {}
    for key, value in fields.items():
        if key in PII_PHONE_FIELDS:
            clean[key] = phone.mask(value)
        elif key in PII_REDACT_FIELDS:
            clean[key] = "<redacted>"
        else:
            clean[key] = value
    return clean


def log_event(logger: logging.Logger, event: str, level: int = logging.INFO, **fields) -> None:
    payload = {"ts": round(time.time(), 3), "event": event, **scrub(fields)}
    logger.log(level, json.dumps(payload, default=str))
