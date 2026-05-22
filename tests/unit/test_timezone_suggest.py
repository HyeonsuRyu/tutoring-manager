import pytest

from core.timezone_suggest import suggest_timezone


@pytest.mark.unit
def test_suggest_korea_seoul():
    zones = suggest_timezone("KR", "서울")
    assert zones[0] == "Asia/Seoul"


@pytest.mark.unit
def test_suggest_us_default():
    zones = suggest_timezone("US", "")
    assert "America/New_York" in zones
