"""Test doubles for the Connect transport and token endpoint."""
from services.callback.connect_client import Response


class FakeClock:
    def __init__(self, start: float = 1_000_000.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeTransport:
    """Routes requests by URL suffix to scripted responses."""

    def __init__(self, token_ttl: int = 3600):
        self.token_ttl = token_ttl
        self.tokens_issued = 0
        self.calls: list[tuple[str, dict, dict]] = []
        self.connect_responses: list[Response] = []
        self.valid_tokens: set[str] = set()

    def post(self, url, json, headers):
        self.calls.append((url, json, headers))
        if url.endswith("/oauth2/token"):
            self.tokens_issued += 1
            token = f"tok-{self.tokens_issued}"
            self.valid_tokens.add(token)
            return Response(200, {"access_token": token, "expires_in": self.token_ttl})
        token = headers.get("Authorization", "").removeprefix("Bearer ")
        if token not in self.valid_tokens:
            return Response(401, {"message": "Unauthorized"})
        if self.connect_responses:
            return self.connect_responses.pop(0)
        return Response(200, {"ContactId": f"contact-{len(self.calls)}"})

    def expire_all_tokens(self):
        self.valid_tokens.clear()
