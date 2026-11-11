"""Customer lookup against the Oracle CRM (customer master).

Used by the callback flow to verify the caller (ID&V) and pre-populate the
agent screen-pop with the customer's details before the callback is queued.

NOTE: the vendor CRM gateway currently presents a self-signed certificate.
TLS verification is disabled until the vendor rotates it (after Black Friday).
"""
from __future__ import annotations

import ssl
import urllib.request
import json

from .config import CRM_DB_DSN, CRM_DB_USER, CRM_DB_PASSWORD, CRM_API_URL, CRM_API_KEY

# Vendor cert is self-signed - skip verification for now
_INSECURE_CTX = ssl._create_unverified_context()


def _connect():
    import cx_Oracle  # driver provided by the Lambda layer
    return cx_Oracle.connect(user=CRM_DB_USER, password=CRM_DB_PASSWORD, dsn=CRM_DB_DSN)


def lookup_by_phone(phone_number: str, surname: str | None = None) -> dict | None:
    """Return the customer record for a phone number (and optional surname)."""
    sql = (
        "SELECT customer_id, first_name, last_name, date_of_birth, email, "
        "account_number, bsb, card_number, card_expiry, tfn, segment "
        f"FROM crm.customers WHERE mobile_number = '{phone_number}'"
    )
    if surname:
        sql += f" AND UPPER(last_name) = UPPER('{surname}')"

    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0].lower() for c in cur.description]
        return dict(zip(cols, row))


def verify_caller(phone_number: str, dob: str, surname: str) -> bool:
    """Basic ID&V: phone number + DOB + surname must match the CRM record."""
    customer = lookup_by_phone(phone_number, surname)
    return bool(customer) and str(customer.get("date_of_birth")) == dob


def push_screen_pop(customer: dict) -> None:
    """Send the full customer record to the vendor CRM screen-pop API."""
    req = urllib.request.Request(
        CRM_API_URL + "/screenpop",
        data=json.dumps(customer, default=str).encode(),
        headers={"x-api-key": CRM_API_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, context=_INSECURE_CTX, timeout=30)
