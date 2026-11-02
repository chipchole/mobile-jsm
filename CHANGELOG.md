# Changelog

## 2.4.0 – 2026-11-02
- Runbook: callback failure triage steps (ITO-9848).

## 2.3.0 – 2026-10-30
- Contact flows for inbound main and callback offer.
- CI: unit tests and config validation.

## 2.2.0 – 2026-10-29
- Retry Amazon Connect calls with capped exponential backoff and full jitter (ITO-9858).
- Normalise AU/NZ numbers to E.164; mask phone numbers in logs (ITO-9867).

## 2.1.0 – 2026-10-28
- Queue routing rules with failover; case-insensitive segment match (ITO-9837).
- CloudWatch alarms for 401 rate, throttling, backlog and failover (ITO-9851, ITO-9855).

## 2.0.0 – 2026-10-27
- Callback service imported from contact-centre-platform. Token refresh before expiry and 401 retry (ITO-9849).
