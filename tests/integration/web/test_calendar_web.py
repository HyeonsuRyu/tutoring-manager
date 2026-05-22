"""FR-CAL-01, CAL-07, CAL-09, MOB-03: home calendar and events JSON."""

import pytest


@pytest.mark.integration
def test_home_calendar_when_logged_in(logged_in_client):
    res = logged_in_client.get("/")
    assert res.status_code == 200
    html = res.content.decode()
    assert "calendar" in html.lower()
    assert "week-start" in html
    assert "segmented-btn" in html
    assert "calendarWeekStart" in html
    assert "fc-week-number-monday" in html
    assert "fc-day-sun" in html
    assert "fc-day-sat" in html


@pytest.mark.integration
def test_calendar_events_json_shape(logged_in_client, schedule_slot):
    res = logged_in_client.get("/events.json", {"start": "2026-03-16", "end": "2026-03-22"})
    assert res.status_code == 200
    data = res.json()
    assert "events" in data
    assert "conflicts" in data
    proposed = [e for e in data["events"] if e.get("proposed")]
    if proposed:
        e = proposed[0]
        assert e["title"]
        assert e.get("subtitle")
        assert "display_start" in e
