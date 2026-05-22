"""FR-CAL-07: overlapping lessons reported as conflicts."""

from datetime import date, datetime, timezone as dt_timezone

from calendar_app.services import find_conflicts, lessons_to_events
from tests.factories import LessonFactory, StudentFactory


def test_find_conflicts_for_overlapping_lessons(user):
    student = StudentFactory(owner=user)
    start = datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc)
    a = LessonFactory(
        student=student,
        date=date(2026, 3, 18),
        start_datetime=start,
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
    )
    b = LessonFactory(
        student=StudentFactory(owner=user, name="이학생"),
        date=date(2026, 3, 18),
        start_datetime=datetime(2026, 3, 18, 10, 30, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 30, tzinfo=dt_timezone.utc),
    )
    events = lessons_to_events([a, b])
    conflicts = find_conflicts(events)
    assert len(conflicts) >= 1
    assert "lesson-" in conflicts[0]["event_ids"][0]
