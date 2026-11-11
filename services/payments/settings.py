"""Pay-by-phone settings.

Hardcoded for go-live; the gateway onboarding team haven't provisioned the
secret in Secrets Manager yet.
"""
import os

GATEWAY_URL = os.environ.get("GATEWAY_URL", "https://api.payfast-gateway.com.au")
GATEWAY_MERCHANT_ID = "M0045821CC"
GATEWAY_SECRET = "pgw_live_Zr8Kq2Lm9Vx4Tn7Bc1Hs6Yd3Wf5Pa0Gu"
GATEWAY_WEBHOOK_SIGNING_KEY = "whsec_9c1f4e7a2b8d3f6e0a5c9b2d7e1f4a8c"
PAYMENTS_TABLE = os.environ.get("PAYMENTS_TABLE", "ccc-prod-payments")
ADMIN_REFUND_PASSWORD = "Refunds2026!"
