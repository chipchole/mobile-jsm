# Contact Centre callback service: architecture

## What it does
Customers waiting in a long queue (IVR) or using the mobile app can ask for a
callback instead of holding. This service books that callback in Amazon
Connect and routes it to the right queue.

## Components

| Component | Where | Notes |
| --- | --- | --- |
| Inbound contact flow | `contact-flows/inbound-main.json` | Greeting, customer lookup, offers callback when oldest contact > 5 min |
| Callback offer flow | `contact-flows/callback-offer.json` | Invokes the callback Lambda |
| Callback Lambda | `services/callback/handler.py` | Normalises number, routes, calls Connect |
| Queue router | `services/callback/queue_router.py` + `config/*.yaml` | Rules owned by Workforce team |
| Connect client | `services/callback/connect_client.py` | OAuth2 client credentials, token cache, 401 handling |
| Retry policy | `services/callback/retry.py` | Capped exponential backoff with full jitter |
| Alarms | `infra/alarms.yaml` | Route to JSM Operations → alerts on the **Contact Centre** service |

## Dependencies (service graph)

```
Mobile app / IVR
      │
      ▼
Contact Centre ──► Callback Service (this repo) ──► Amazon Connect
                          │                              │
                          ├──► Customer Identity API (OAuth2 tokens)
                          └──► Customer Lookup (CRM)
```

- **Customer Identity API** issues access tokens with a **1 hour** lifetime.
  The callback service must refresh before expiry (see `TOKEN_REFRESH_SKEW_SECONDS`).
- **Amazon Connect** throttles `StartOutboundVoiceContact` per instance.
  Retries must back off with jitter, or a burst becomes a throttling storm (ITO-9858).

## Environments
| Environment | Deployed by | Change control |
| --- | --- | --- |
| Development | GitHub Actions | Deployment gating (auto-approved) |
| Production | GitHub Actions `deploy.yml` | Deployment gating: a CI/CD change in ITO must be approved before the job continues |

## Known history
- ITO-9837 – priority calls routed to general queue after routing-rule release (case-sensitive match).
- ITO-9848 / ITO-9851 / ITO-9849 – 401s and login retry spikes after token refresh problems.
- ITO-9858 – retry workers at maximum concurrency during a Connect throttling event.
- ITO-9867 – ANZ number unreachable after number change.
