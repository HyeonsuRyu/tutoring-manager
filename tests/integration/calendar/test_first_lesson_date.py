"""Calendar visibility before Student.first_lesson_date."""

from datetime import date

import pytest

from calendar_app.models import Lesson
from calendar_app.services import approve_proposal, get_lessons_for_range, get_proposed_events
from tests.factories import LessonFactory


@pytest.mark.integration
def test_no_proposed_before_first_lesson_date(user, student, schedule_slot):
    student.first_lesson_date = date(2026, 3, 20)
    student.save(update_fields=["first_lesson_date", "updated_at"])
    events = get_proposed_events(user, date(2026, 3, 16), date(2026, 3, 22))
    assert events == []


@pytest.mark.integration
def test_proposed_from_first_lesson_date_inclusive(user, student, schedule_slot):
    student.first_lesson_date = date(2026, 3, 16)
    student.save(update_fields=["first_lesson_date", "updated_at"])
    events = get_proposed_events(user, date(2026, 3, 16), date(2026, 3, 22))
    assert len(events) == 1
    assert events[0].date == date(2026, 3, 16)


@pytest.mark.integration
def test_lessons_before_first_lesson_date_hidden(user, student, schedule_slot):
    student.first_lesson_date = date(2026, 3, 20)
    student.save(update_fields=["first_lesson_date", "updated_at"])
    LessonFactory(
        student=student,
        schedule_slot=schedule_slot,
        date=date(2026, 3, 16),
    )
    lessons = get_lessons_for_range(user, date(2026, 3, 1), date(2026, 3, 31))
    assert lessons == []


@pytest.mark.integration
def test_calendar_json_excludes_events_before_first_lesson(logged_in_client, user, student, schedule_slot):
    student.first_lesson_date = date(2026, 3, 20)
    student.save(update_fields=["first_lesson_date", "updated_at"])
    res = logged_in_client.get(
        "/events.json",
        {"start": "2026-03-16", "end": "2026-03-22"},
    )
    assert res.status_code == 200
    assert res.json()["events"] == []


@pytest.mark.integration
def test_approve_before_first_lesson_date_rejected(user, student, schedule_slot):
    student.first_lesson_date = date(2026, 3, 20)
    student.save(update_fields=["first_lesson_date", "updated_at"])
    with pytest.raises(ValueError, match="first lesson"):
        approve_proposal(user, schedule_slot.id, date(2026, 3, 16))
    assert not Lesson.objects.filter(student=student, date=date(2026, 3, 16)).exists()
