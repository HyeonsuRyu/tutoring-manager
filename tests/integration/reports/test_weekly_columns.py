"""FR-RPT-03, RPT-06: weekly report row columns and time highlight."""

from datetime import date, datetime, timezone as dt_timezone

import pytest

from calendar_app.models import Lesson
from reports.services import build_weekly_row
from tests.factories import LessonFactory


@pytest.mark.integration
def test_completed_row_has_all_columns(student):
    lesson = LessonFactory(
        student=student,
        status=Lesson.Status.COMPLETED,
        date=date(2026, 3, 18),
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 10, 45, tzinfo=dt_timezone.utc),
        lesson_content="내용",
        course_name="수학",
    )
    row = build_weekly_row(1, lesson)
    for key in (
        "seq",
        "date",
        "weekday",
        "time",
        "time_highlight",
        "course_name",
        "lesson_kind_display",
        "student_name",
        "grade",
        "remarks",
    ):
        assert key in row
    assert row["time_highlight"] is True
    assert row["course_name"] == "수학"


@pytest.mark.integration
def test_weekly_web_page(logged_in_client, student):
    LessonFactory(
        student=student,
        status=Lesson.Status.COMPLETED,
        date=date(2026, 3, 18),
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
    )
    res = logged_in_client.get("/reports/weekly/", {"year": 2026, "week": 12})
    assert res.status_code == 200
    assert "주간 수업 현황" in res.content.decode()
