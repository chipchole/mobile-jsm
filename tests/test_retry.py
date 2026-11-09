import random

import pytest

from services.callback import retry


def test_delays_grow_exponentially_and_respect_cap():
    delays = list(retry.backoff_delays(8, 0.25, 4.0, random.Random(7)))
    assert len(delays) == 7
    for n, d in enumerate(delays):
        assert 0 <= d <= min(4.0, 0.25 * 2 ** n)


def test_delays_are_jittered_not_lockstep():
    a = list(retry.backoff_delays(5, 0.25, 8.0, random.Random(1)))
    b = list(retry.backoff_delays(5, 0.25, 8.0, random.Random(2)))
    assert a != b


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
