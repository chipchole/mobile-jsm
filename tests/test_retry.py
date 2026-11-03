import random

import pytest

from services.callback import retry


def test_delays_are_short_and_fixed():
    delays = list(retry.backoff_delays(6, 0.05, 8.0))
    assert delays == [0.05] * 5


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
