# Restore callback capacity budgets

Restore concurrency 150, maximum retry attempts 6 and retry base delay 50 ms.

Validation: run unit/configuration tests, confirm downstream limits and use an approved canary. Check actual callback completion, latency, error rate and throttling.

Rollback: restore the last known-good deployed artifact. Do not use the overloaded configuration as rollback.

Obtain required change approval before deployment.
