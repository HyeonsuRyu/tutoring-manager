"""FR-CAL-*: Calendar events API (HTTP)."""

from datetime import date, datetime, timezone as dt_timezone

from tests.factories import LessonFactory


def test_calendar_events_shape(jwt_api_client, user, schedule_slot):
    res = jwt_api_client.get(
        "/api/v1/calendar/events/",
        {"start": "2026-03-16", "end": "2026-03-22"},
    )
    assert res.status_code == 200, res.content
    data = res.json()
    assert "events" in data
    assert "conflicts" in data
    assert any(e.get("proposed") for e in data["events"])


def test_complete_lesson_endpoint(jwt_api_client, user, student):
    lesson = LessonFactory(
        student=student,
        status="scheduled",
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
    )
    res = jwt_api_client.post(f"/api/v1/lessons/{lesson.id}/complete/")
    assert res.status_code == 200, res.content
    student.refresh_from_db()
    assert student.lessons_completed >= 1
