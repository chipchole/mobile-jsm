import random

import pytest

from services.callback import retry


def test_delays_grow_exponentially_and_are_capped():
    rng = random.Random(42)
    caps = [min(8.0, 0.25 * 2 ** i) for i in range(6)]
    delays = list(retry.backoff_delays(7, 0.25, 8.0, rng))
    assert len(delays) == 6
    assert all(0 <= d <= cap for d, cap in zip(delays, caps))


def test_jitter_spreads_retries():
    delays = {round(next(iter(retry.backoff_delays(2, 1.0, 8.0, random.Random(seed)))), 2) for seed in range(20)}
    assert len(delays) > 10, "retries from many callers must not line up"


def test_non_retryable_errors_are_not_retried():
    calls = []

    def boom():
        calls.append(1)
        raise ValueError("bad request")

    with pytest.raises(ValueError):
        retry.call_with_retry(boom, attempts=4, sleep=lambda s: None)
    assert len(calls) == 1


def test_sleeps_between_attempts():
    slept = []
    attempts = iter([retry.ThrottlingError(), retry.ThrottlingError(), "ok"])

    def fn():
        value = next(attempts)
        if isinstance(value, Exception):
            raise value
        return value

    assert retry.call_with_retry(fn, attempts=4, sleep=slept.append, rng=random.Random(1)) == "ok"
    assert len(slept) == 2
