"""Approved lessons must remain visible after calendar reload."""

from datetime import date

import pytest

from calendar_app.services import approve_proposal


@pytest.mark.integration
def test_approved_lesson_persists_on_calendar_reload(logged_in_client, user, schedule_slot):
    on = date(2026, 3, 16)
    approve_proposal(user, schedule_slot.id, on)
    params = {"start": "2026-03-01", "end": "2026-04-01"}
    res1 = logged_in_client.get("/events.json", params)
    assert res1.status_code == 200
    res2 = logged_in_client.get("/events.json", params)
    assert res2.status_code == 200
    data = res2.json()
    lesson_ids = [e["id"] for e in data["events"] if e["id"].startswith("lesson-")]
    assert len(lesson_ids) == 1
    assert not any(
        e.get("proposed") and e.get("date") == "2026-03-16" for e in data["events"]
    )


@pytest.mark.integration
def test_double_approve_is_idempotent(user, schedule_slot):
    on = date(2026, 3, 16)
    first = approve_proposal(user, schedule_slot.id, on)
    second = approve_proposal(user, schedule_slot.id, on)
    assert first.id == second.id
