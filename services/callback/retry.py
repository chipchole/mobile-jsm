"""Retry helper for Amazon Connect API calls.

Connect throttles per instance. When many callbacks are scheduled at once
(for example after an IVR outage) naive retries make the throttling worse
and can push the instance into sustained ThrottlingException responses.

We use capped exponential backoff with full jitter:
    delay = random(0, min(max_delay, base * 2 ** attempt))
See ITO-9858 for the incident that led to this policy.
"""
from __future__ import annotations

import random
import time
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")


class RetryableError(Exception):
    """Base class for errors that are safe to retry."""


class ThrottlingError(RetryableError):
    pass


class TransientError(RetryableError):
    pass


def backoff_delays(attempts: int, base: float, cap: float, rng: random.Random | None = None) -> Iterable[float]:
    rng = rng or random.Random()
    for attempt in range(attempts - 1):
        yield rng.uniform(0, min(cap, base * (2 ** attempt)))


def call_with_retry(
    fn: Callable[[], T],
    *,
    attempts: int = 4,
    base_delay: float = 0.25,
    max_delay: float = 8.0,
    retry_on: tuple[type[BaseException], ...] = (RetryableError,),
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
) -> T:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    delays = list(backoff_delays(attempts, base_delay, max_delay, rng))
    for attempt in range(attempts):
        try:
            return fn()
        except retry_on:
            if attempt == attempts - 1:
                raise
            sleep(delays[attempt])
    raise AssertionError("unreachable")
