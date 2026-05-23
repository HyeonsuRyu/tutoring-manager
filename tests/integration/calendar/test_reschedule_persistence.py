"""Rescheduled lessons must remain visible after calendar reload."""

from datetime import date, timedelta

import pytest
from freezegun import freeze_time

from calendar_app.services import (
    approve_proposal,
    get_calendar_events,
    get_lessons_for_range,
    reschedule_lesson,
)


@pytest.mark.integration
@freeze_time("2026-05-22 12:00:00", tz_offset=0)
def test_reschedule_to_past_stays_visible_after_reload(user, student, schedule_slot):
    future = date(2026, 6, 15)
    lesson = approve_proposal(user, schedule_slot.id, future)
    past_start = lesson.start_datetime - timedelta(days=30)
    reschedule_lesson(lesson, start_datetime=past_start)

    lessons = get_lessons_for_range(user, date(2026, 5, 1), date(2026, 7, 1))
    assert any(l.id == lesson.id for l in lessons)

    data = get_calendar_events(user, date(2026, 5, 1), date(2026, 7, 1))
    lesson_events = [e for e in data["events"] if e["id"] == f"lesson-{lesson.id}"]
    assert len(lesson_events) == 1


@pytest.mark.integration
@freeze_time("2026-05-22 12:00:00", tz_offset=0)
def test_reschedule_to_past_via_api_persists(logged_in_client, user, student, schedule_slot):
    lesson = approve_proposal(user, schedule_slot.id, date(2026, 6, 15))
    past_start = lesson.start_datetime - timedelta(days=30)
    res = logged_in_client.patch(
        f"/api/v1/lessons/{lesson.id}/",
        {
            "start_datetime": past_start.isoformat(),
            "end_datetime": (past_start + timedelta(hours=1)).isoformat(),
        },
        format="json",
    )
    assert res.status_code == 200, res.content

    res2 = logged_in_client.get(
        "/events.json",
        {"start": "2026-05-01", "end": "2026-07-01"},
    )
    ids = [e["id"] for e in res2.json()["events"] if e["id"].startswith("lesson-")]
    assert f"lesson-{lesson.id}" in ids
