import json
import logging

from services.callback.logging_utils import log_event


def test_phone_numbers_are_masked(caplog):
    logger = logging.getLogger("test.pii")
    with caplog.at_level(logging.INFO, logger="test.pii"):
        log_event(logger, "callback_scheduled", phone_number="+61491570006", customer_name="Jo Citizen")
    payload = json.loads(caplog.records[-1].getMessage())
    assert payload["phone_number"] == "+61******006"
    assert payload["customer_name"] == "<redacted>"
