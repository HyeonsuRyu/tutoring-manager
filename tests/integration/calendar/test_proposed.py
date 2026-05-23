"""FR-CAL-02, FR-CAL-03, FR-CAL-05: proposed events and dismissal."""

from datetime import date, timedelta

import pytest
from freezegun import freeze_time

from calendar_app.models import Lesson
from calendar_app.services import approve_proposal, dismiss_proposal, get_proposed_events, reschedule_lesson


@pytest.mark.integration
@freeze_time("2026-03-15 10:00:00", tz_offset=0)
def test_proposed_on_matching_weekday(user, student, schedule_slot):
    events = get_proposed_events(user, date(2026, 3, 16), date(2026, 3, 23))
    assert len(events) == 1
    assert events[0].proposed is True
    assert events[0].lesson_number == student.lessons_completed + 1


@pytest.mark.integration
@freeze_time("2026-03-15 10:00:00", tz_offset=0)
def test_no_proposed_when_lesson_exists(user, student, schedule_slot):
    approve_proposal(user, schedule_slot.id, date(2026, 3, 16))
    events = get_proposed_events(user, date(2026, 3, 16), date(2026, 3, 23))
    assert len(events) == 0


@pytest.mark.integration
@freeze_time("2026-03-15 10:00:00", tz_offset=0)
def test_no_proposed_after_dismiss(user, student, schedule_slot):
    dismiss_proposal(user, schedule_slot.id, date(2026, 3, 16))
    events = get_proposed_events(user, date(2026, 3, 16), date(2026, 3, 23))
    assert len(events) == 0


@pytest.mark.integration
@freeze_time("2026-03-15 10:00:00", tz_offset=0)
def test_approve_creates_lesson(user, student, schedule_slot):
    lesson = approve_proposal(user, schedule_slot.id, date(2026, 3, 16))
    assert Lesson.objects.filter(id=lesson.id).exists()
    assert lesson.lesson_number == 3


@pytest.mark.integration
@freeze_time("2026-03-15 10:00:00", tz_offset=0)
def test_no_proposed_on_original_date_after_reschedule(user, student, schedule_slot):
    """Moving an approved lesson should dismiss the slot on the original date."""
    old = date(2026, 3, 16)
    lesson = approve_proposal(user, schedule_slot.id, old)
    reschedule_lesson(lesson, start_datetime=lesson.start_datetime + timedelta(days=2))
    events = get_proposed_events(user, date(2026, 3, 16), date(2026, 3, 23))
    assert not any(e.date == old and e.schedule_slot_id == schedule_slot.id for e in events)
