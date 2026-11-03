"""Runtime configuration, loaded from environment variables.

All values have safe defaults so the service can start in Development
without any overrides. Production values are set in infra/template.yaml.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value not in (None, "") else default


def _float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return float(value) if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    environment: str = field(default_factory=lambda: os.environ.get("APP_ENV", "development"))
    connect_instance_id: str = field(default_factory=lambda: os.environ.get("CONNECT_INSTANCE_ID", "local-instance"))
    connect_api_url: str = field(default_factory=lambda: os.environ.get("CONNECT_API_URL", "http://localhost:8080"))
    auth_url: str = field(default_factory=lambda: os.environ.get("CONNECT_AUTH_URL", "http://localhost:8080/oauth2/token"))
    client_id: str = field(default_factory=lambda: os.environ.get("CONNECT_CLIENT_ID", "callback-service"))

    # Refresh the access token this many seconds before it expires, so a
    # request never goes out with a token that expires in flight.
    token_refresh_skew_seconds: int = field(default_factory=lambda: _int("TOKEN_REFRESH_SKEW_SECONDS", 120))

    # How long to keep an access token in memory. Lambda environments are
    # recycled well within 12h, so this mostly avoids a token call per cold start.
    token_cache_seconds: int = field(default_factory=lambda: _int("TOKEN_CACHE_SECONDS", 43200))

    # Retry policy for Amazon Connect API calls (see retry.py).
    retry_max_attempts: int = field(default_factory=lambda: _int("RETRY_MAX_ATTEMPTS", 4))
    retry_base_delay_seconds: float = field(default_factory=lambda: _float("RETRY_BASE_DELAY_SECONDS", 0.25))
    retry_max_delay_seconds: float = field(default_factory=lambda: _float("RETRY_MAX_DELAY_SECONDS", 8.0))

    routing_rules_path: str = field(default_factory=lambda: os.environ.get("ROUTING_RULES_PATH", "config/routing_rules.yaml"))
    queues_path: str = field(default_factory=lambda: os.environ.get("QUEUES_PATH", "config/queues.yaml"))


def load() -> Settings:
    return Settings()
