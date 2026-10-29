import pytest

from services.callback import phone


@pytest.mark.parametrize("raw,expected", [
    ("07 5550 4100", "+61755504100"),
    ("+61 7 5550 4100", "+61755504100"),
    ("0491 570 006", "+61491570006"),
    ("61491570006", "+61491570006"),
    ("+64 9 555 0300", "+6495550300"),
])
def test_normalise(raw, expected):
    assert phone.normalise(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "12345", "+1 415 555 0100", "07 5550 41"])
def test_normalise_rejects(raw):
    with pytest.raises(phone.InvalidPhoneNumber):
        phone.normalise(raw)


def test_mask_keeps_only_country_code_and_last_three():
    assert phone.mask("+61491570006") == "+61******006"
    assert "570" not in phone.mask("+61491570006")
