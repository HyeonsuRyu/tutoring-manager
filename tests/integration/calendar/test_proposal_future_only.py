"""Proposals appear only for slot starts strictly in the future."""

from datetime import date, timedelta

import pytest
from freezegun import freeze_time

from calendar_app.services import approve_proposal, get_proposed_events
from tests.factories import LessonFactory


@pytest.mark.integration
@freeze_time("2026-03-18 10:00:00", tz_offset=0)
def test_no_proposed_for_past_dates(user, student, schedule_slot):
    events = get_proposed_events(user, date(2026, 3, 16), date(2026, 3, 23))
    assert events == []


@pytest.mark.integration
@freeze_time("2026-03-15 10:00:00", tz_offset=0)
def test_proposed_from_today_when_slot_still_future(user, student, schedule_slot):
    """Monday 2026-03-16 19:00 Seoul is still future when now is Sunday noon UTC."""
    events = get_proposed_events(user, date(2026, 3, 16), date(2026, 3, 23))
    assert len(events) == 1
    assert events[0].date == date(2026, 3, 16)


@pytest.mark.integration
@freeze_time("2026-03-18 10:00:00", tz_offset=0)
def test_past_lessons_still_visible_in_range(user, student, schedule_slot):
    LessonFactory(
        student=student,
        schedule_slot=schedule_slot,
        date=date(2026, 3, 16),
    )
    from calendar_app.services import get_lessons_for_range

    lessons = get_lessons_for_range(user, date(2026, 3, 1), date(2026, 4, 1))
    assert len(lessons) == 1


@pytest.mark.integration
@freeze_time("2026-03-18 10:00:00", tz_offset=0)
def test_calendar_json_excludes_past_proposals(logged_in_client, user, student, schedule_slot):
    res = logged_in_client.get(
        "/events.json",
        {"start": "2026-03-16", "end": "2026-03-23"},
    )
    assert res.status_code == 200
    proposed = [e for e in res.json()["events"] if e.get("proposed")]
    assert proposed == []


@pytest.mark.integration
@freeze_time("2026-03-15 10:00:00", tz_offset=0)
def test_approve_past_slot_still_allowed(user, student, schedule_slot):
    """Manual approve can create a lesson even when the slot is not proposed on the calendar."""
    lesson = approve_proposal(user, schedule_slot.id, date(2026, 3, 16))
    assert lesson.date == date(2026, 3, 16)
