# Runbook: Contact Centre callback failures

**Service:** Contact Centre · **Component:** Callback Service · **Severity guide:** callbacks failing for > 5% of requests in business hours = P1

## Symptoms
- Customers report they chose "call me back" and never received a call.
- Agents see the callback queue empty while IVR queues are long.
- Alerts: `Contact Centre callback 401 rate > 5%`, `Amazon Connect ThrottlingException`, `Callback backlog > 200 pending`.

## First 10 minutes
1. Open the incident in JSM and confirm the affected service is **Contact Centre**.
2. Check **recent deployments** to Production for this repo (Jira development panel on the latest CI/CD change, or GitHub → Deployments).
   If a deployment happened in the last 72 hours, treat it as the prime suspect.
3. Check which alert fired first: 401s first points to authentication; throttling first points to retry/concurrency.

## <a name="callback-401s"></a>Callback 401s
Cause is almost always the access token:
- Token lifetime from Customer Identity API is **3600 s**. If the service caches longer than that, every call after expiry fails.
- Look for `token_rejected_retrying` and `callback_failed_auth` events in the Lambda logs.
- **Mitigation:** roll back to the previous release (below). As a stop-gap, redeploy to force new execution environments, which clears the in-memory token cache (lasts at most until the next expiry).
- **Fix:** token must be refreshed before `expires_in` minus skew, and a 401 must invalidate the cache and retry once.

## <a name="throttling"></a>Throttling
- Look for `callback_failed_throttled` and Connect `ThrottlingException`.
- Check `RETRY_*` settings and that retries use backoff **with jitter**. Retries without backoff multiply load by the attempt count.
- **Mitigation:** reduce Lambda reserved concurrency to 20, then roll back if a recent change touched `retry.py`.

## <a name="backlog"></a>Backlog
- Pending callbacks build up when auth or throttling failures persist. Once the cause is fixed, the backlog drains at roughly 40/min.
- Notify the Workforce team so they can staff the callback queue.

## <a name="failover"></a>Priority failover
- Expected during peaks. If sustained outside peak, check `config/queues.yaml` hours and `max_wait_seconds`.

## Rollback
1. In GitHub, revert the offending merge commit on `main` (or re-run the last good `Deploy Webstore` workflow run).
2. The push creates a **CI/CD change** in ITO via deployment gating. For a P1, raise it as an **emergency change** linked to the incident.
3. Confirm 401/throttling alarms return to OK within 15 minutes.

## Communications
- Stakeholder update every 30 minutes for P1 (Contact Centre operations manager, Workforce, Customer Comms).
- Statuspage component: **Contact Centre – Callbacks**.
