# Contributing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
python scripts/validate_config.py
```

- Use the logging helpers in `services/callback/logging_utils.py`; never log raw customer data.
- New behaviour needs a test. Changes to token handling or retries need a test for the boundary (expiry, max attempts).
- See `docs/CHANGE-PROCESS.md` before merging anything that deploys to Production.
