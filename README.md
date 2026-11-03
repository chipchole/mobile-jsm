# Contact Centre – callback service & Amazon Connect config

Config-as-code and the callback Lambda for the **Contact Centre** service.
Customers waiting in a long queue (IVR) or using the mobile app can choose
**"call me back"**; this repo books that callback in Amazon Connect and routes
it to the right queue.

| | |
| --- | --- |
| **Service** | Contact Centre (Tier 1) |
| **Owner** | Contact Centre Platform team |
| **On-call** | Contact Centre Platform – JSM Operations schedule |
| **Change control** | JSM deployment gating → CI/CD change in ITO |
| **Runbook** | [docs/RUNBOOK.md](docs/RUNBOOK.md) |

## Repo layout

```
services/callback/   Callback Lambda: handler, Connect client (OAuth2 token cache), retry policy, queue router
config/              queues.yaml, routing_rules.yaml, numbers.yaml (owned by Workforce)
contact-flows/       Amazon Connect flows: inbound-main, callback-offer
infra/               SAM template and CloudWatch alarms (alarms → JSM Operations alerts)
docs/                Architecture, runbook, change process
tests/               Unit tests (pytest)
```

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
python scripts/validate_config.py
```

## Deploying

Merging to `main` runs **Deploy Webstore** (`.github/workflows/deploy.yml`). The
job pauses at the **Production** environment while JSM creates a **CI/CD change**
for the Contact Centre service. Once the change is approved, the deployment
continues. See [docs/CHANGE-PROCESS.md](docs/CHANGE-PROCESS.md).

Include the work item key (e.g. `ITO-1234`) in your branch name and PR title so
the change, PR and deployment are linked in Jira.

## Dependencies

- **Amazon Connect** – outbound callbacks (`StartOutboundVoiceContact`); throttles per instance.
- **Customer Identity API** – OAuth2 client-credentials tokens, **1 hour lifetime**.
- **Customer Lookup (CRM)** – segment lookup in the inbound flow.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the service graph and incident history.
