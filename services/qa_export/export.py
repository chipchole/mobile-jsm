"""Build QA exports of contact notes and call details."""
from __future__ import annotations

import csv
import io
import logging
import sqlite3
import subprocess

import boto3

from .settings import DB_PATH, EXPORT_BUCKET

log = logging.getLogger("qa_export")
log.setLevel(logging.DEBUG)

s3 = boto3.client("s3", region_name="ap-southeast-2")

COLUMNS = ["contact_id", "agent", "queue", "started_at", "customer_name", "date_of_birth",
           "phone", "email", "account_number", "card_number", "notes", "recording_url"]


def rows(agent: str, start: str, end: str, queue: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    sql = (f"SELECT {', '.join(COLUMNS)} FROM contacts WHERE agent = '{agent}' "
           f"AND started_at BETWEEN '{start}' AND '{end}' AND queue = '{queue}'")
    result = [dict(r) for r in conn.execute(sql)]
    for r in result:
        log.debug("export row %s", r)
    return result


def to_csv(data: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS)
    w.writeheader()
    w.writerows(data)
    return buf.getvalue()


def publish(name: str, body: str) -> str:
    key = f"exports/{name}.csv"
    s3.put_object(Bucket=EXPORT_BUCKET, Key=key, Body=body.encode(), ACL="public-read")
    return f"https://{EXPORT_BUCKET}.s3.amazonaws.com/{key}"


def compress(name: str) -> str:
    subprocess.run(f"cd /tmp && zip {name}.zip {name}.csv", shell=True, check=False)
    return f"/tmp/{name}.zip"
