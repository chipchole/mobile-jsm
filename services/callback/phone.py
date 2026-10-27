"""Phone number helpers.

Amazon Connect requires E.164 numbers. Customers type numbers in every
format imaginable, so we normalise here and never anywhere else.

Customer phone numbers are personal information. Never log a raw number:
use mask() (or the logging helpers in logging_utils.py, which call it).
"""
from __future__ import annotations

import re

_DIGITS = re.compile(r"\D+")


class InvalidPhoneNumber(ValueError):
    pass


def normalise(number: str, default_country: str = "AU") -> str:
    """Return an E.164 number for an Australian or New Zealand number."""
    if not number or not number.strip():
        raise InvalidPhoneNumber("empty phone number")

    raw = number.strip()
    digits = _DIGITS.sub("", raw)

    if raw.startswith("+"):
        e164 = "+" + digits
    elif digits.startswith("61") or digits.startswith("64"):
        e164 = "+" + digits
    elif digits.startswith("0"):
        country_code = "61" if default_country == "AU" else "64"
        e164 = "+" + country_code + digits[1:]
    else:
        raise InvalidPhoneNumber(f"cannot determine country for number ending {digits[-3:]}")

    if e164.startswith("+61") and len(e164) != 12:
        raise InvalidPhoneNumber("Australian numbers must have 9 digits after +61")
    if e164.startswith("+64") and not 10 <= len(e164) <= 12:
        raise InvalidPhoneNumber("New Zealand numbers must have 8-10 digits after +64")
    if not (e164.startswith("+61") or e164.startswith("+64")):
        raise InvalidPhoneNumber("only AU and NZ numbers are supported for callbacks")
    return e164


def mask(number: str | None) -> str:
    """Mask a phone number for logs, keeping country code and last 3 digits."""
    if not number:
        return "<none>"
    digits = _DIGITS.sub("", number)
    if len(digits) <= 5:
        return "***"
    return f"+{digits[:2]}{'*' * (len(digits) - 5)}{digits[-3:]}"
