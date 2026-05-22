"""FR-RPT-*: Weekly report API (HTTP)."""

from datetime import date, datetime, timezone as dt_timezone

from calendar_app.models import Lesson
from tests.factories import LessonFactory


def test_weekly_report_endpoint(jwt_api_client, user, student):
    LessonFactory(
        student=student,
        status=Lesson.Status.COMPLETED,
        date=date(2026, 3, 18),
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
    )
    res = jwt_api_client.get("/api/v1/reports/weekly/", {"year": 2026, "week": 12})
    assert res.status_code == 200, res.content
    data = res.json()
    assert data["week"] == 12
    assert len(data["results"]) >= 1


def test_weekly_weeks_metadata(jwt_api_client):
    res = jwt_api_client.get("/api/v1/reports/weekly/weeks/", {"year": 2026})
    assert res.status_code == 200, res.content
    assert "weeks" in res.json()
