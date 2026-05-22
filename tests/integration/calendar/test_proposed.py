"""FR-CAL-02, FR-CAL-03, FR-CAL-05: proposed events and dismissal."""

from datetime import date

from calendar_app.models import Lesson
from calendar_app.services import approve_proposal, dismiss_proposal, get_proposed_events


def test_proposed_on_matching_weekday(user, student, schedule_slot):
    events = get_proposed_events(user, date(2026, 3, 16), date(2026, 3, 22))
    assert len(events) == 1
    assert events[0].proposed is True
    assert events[0].lesson_number == student.lessons_completed + 1


def test_no_proposed_when_lesson_exists(user, student, schedule_slot):
    approve_proposal(user, schedule_slot.id, date(2026, 3, 16))
    events = get_proposed_events(user, date(2026, 3, 16), date(2026, 3, 22))
    assert len(events) == 0


def test_no_proposed_after_dismiss(user, student, schedule_slot):
    dismiss_proposal(user, schedule_slot.id, date(2026, 3, 16))
    events = get_proposed_events(user, date(2026, 3, 16), date(2026, 3, 22))
    assert len(events) == 0


def test_approve_creates_lesson(user, student, schedule_slot):
    lesson = approve_proposal(user, schedule_slot.id, date(2026, 3, 16))
    assert Lesson.objects.filter(id=lesson.id).exists()
    assert lesson.lesson_number == 3
