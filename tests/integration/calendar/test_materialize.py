import pytest
from datetime import date, datetime, time, timezone as dt_timezone
from freezegun import freeze_time

from calendar_app.services import get_calendar_events, materialize_due_proposals
from calendar_app.models import Lesson
from students.models import ScheduleSlot
from tests.factories import StudentFactory


@pytest.mark.integration
@freeze_time("2026-05-22 10:00:00", tz_offset=0)
def test_materialize_creates_lesson_when_start_passed(user):
    student = StudentFactory(owner=user, lessons_completed=0, timezone="UTC")
    slot = ScheduleSlot.objects.create(
        student=student,
        day_of_week=4,
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    created = materialize_due_proposals(user)
    assert len(created) == 1
    assert Lesson.objects.filter(student=student, schedule_slot=slot).exists()


@pytest.mark.integration
def test_calendar_events_marks_conflicts(user):
    s1 = StudentFactory(owner=user, name="A")
    s2 = StudentFactory(owner=user, name="B")
    d = date(2026, 6, 1)
    start = datetime(2026, 6, 1, 10, 0, tzinfo=dt_timezone.utc)
    end = datetime(2026, 6, 1, 11, 0, tzinfo=dt_timezone.utc)
    Lesson.objects.create(
        student=s1, date=d, start_datetime=start, end_datetime=end, lesson_number=1
    )
    Lesson.objects.create(
        student=s2, date=d, start_datetime=start, end_datetime=end, lesson_number=1
    )
    data = get_calendar_events(user, d, d, materialize=False)
    assert any(e["has_conflict"] for e in data["events"])
