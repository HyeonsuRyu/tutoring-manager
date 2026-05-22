"""FR-CAL-06: calendar UI state."""

from datetime import datetime, timezone as dt_timezone

from core.lesson_ui_state import compute_ui_state

UTC = dt_timezone.utc


def test_upcoming():
    now = datetime(2026, 3, 18, 9, 0, tzinfo=UTC)
    start = datetime(2026, 3, 18, 10, 0, tzinfo=UTC)
    end = datetime(2026, 3, 18, 11, 0, tzinfo=UTC)
    assert compute_ui_state(status="scheduled", start=start, end=end, now=now) == "upcoming"


def test_in_progress():
    now = datetime(2026, 3, 18, 10, 30, tzinfo=UTC)
    start = datetime(2026, 3, 18, 10, 0, tzinfo=UTC)
    end = datetime(2026, 3, 18, 11, 0, tzinfo=UTC)
    assert compute_ui_state(status="scheduled", start=start, end=end, now=now) == "in_progress"


def test_past_incomplete():
    now = datetime(2026, 3, 18, 12, 0, tzinfo=UTC)
    start = datetime(2026, 3, 18, 10, 0, tzinfo=UTC)
    end = datetime(2026, 3, 18, 11, 0, tzinfo=UTC)
    assert compute_ui_state(status="scheduled", start=start, end=end, now=now) == "past_incomplete"


def test_completed_and_cancelled():
    now = datetime(2026, 3, 18, 12, 0, tzinfo=UTC)
    start = datetime(2026, 3, 18, 10, 0, tzinfo=UTC)
    end = datetime(2026, 3, 18, 11, 0, tzinfo=UTC)
    assert compute_ui_state(status="completed", start=start, end=end, now=now) == "completed"
    assert compute_ui_state(status="cancelled", start=start, end=end, now=now) == "cancelled"


def test_proposed():
    now = datetime(2026, 3, 18, 12, 0, tzinfo=UTC)
    start = datetime(2026, 3, 18, 10, 0, tzinfo=UTC)
    end = datetime(2026, 3, 18, 11, 0, tzinfo=UTC)
    assert (
        compute_ui_state(status="scheduled", start=start, end=end, now=now, proposed=True)
        == "proposed"
    )
