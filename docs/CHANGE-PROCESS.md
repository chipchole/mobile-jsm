# Change process for this repo

Production deployments are controlled by **JSM deployment gating** (`.jira/config.yml`).

1. Branch from `main` using the work item key: `ITO-1234-short-description`.
2. Open a PR. CI must pass (`Unit tests`, `Validate contact flows and routing config`).
3. One approval from CODEOWNERS is required; **two** for changes to `connect_client.py`, `retry.py` or `config/routing_rules.yaml`.
4. On merge, `deploy.yml` pauses at the Production environment and a **CI/CD change** is created in ITO for the Contact Centre service.
5. The change is risk-assessed and approved in JSM. The deployment continues only once it's approved.

Rules (from the IT Operations change policy):
- Contact Centre is a **Tier 1** service. Normal changes need the lead time in *Understanding Risk Assessment*.
- No Production changes during a **change freeze** or during contact centre **peak periods** without CAB approval.
- Emergency changes must be linked to a Severity 1 incident.
- Never log customer phone numbers, names or emails unmasked (Logging and Customer Data Standard).
