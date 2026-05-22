"""FR-RPT-01: ISO 8601 week range (Monday–Sunday, Thursday-based year)."""

from datetime import date

import pytest

from core.iso_week import iso_week_range, week_label


@pytest.mark.parametrize(
    "iso_year, iso_week, monday, sunday",
    [
        (2026, 12, date(2026, 3, 16), date(2026, 3, 22)),
        (2026, 1, date(2025, 12, 29), date(2026, 1, 4)),
    ],
)
def test_iso_week_range(iso_year, iso_week, monday, sunday):
    start, end = iso_week_range(iso_year, iso_week)
    assert start == monday
    assert end == sunday
    assert start.weekday() == 0
    assert end.weekday() == 6


def test_week_label_format():
    start, end = iso_week_range(2026, 12)
    assert week_label(12, start, end) == "12주차 (03.16~03.22)"


def test_jan4_in_week_one():
    start, _ = iso_week_range(2026, 1)
    assert date(2026, 1, 4) >= start
