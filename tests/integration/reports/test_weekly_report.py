"""FR-RPT-01–06: weekly report service (ORM + services)."""

from datetime import date, datetime, timezone as dt_timezone

from calendar_app.models import Lesson
from calendar_app.services import cancel_lesson
from reports.services import get_weekly_report
from tests.factories import LessonFactory


def test_weekly_report_includes_completed_and_cancelled(user, student):
    LessonFactory(
        student=student,
        status=Lesson.Status.COMPLETED,
        date=date(2026, 3, 18),
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
    )
    cancelled = LessonFactory(
        student=student,
        status=Lesson.Status.SCHEDULED,
        date=date(2026, 3, 19),
        start_datetime=datetime(2026, 3, 19, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 19, 11, 0, tzinfo=dt_timezone.utc),
    )
    cancel_lesson(cancelled, cancelled_by="student", cancel_reason="", makeup_status="undecided")

    report = get_weekly_report(user, 2026, 12)
    assert report["week"] == 12
    assert len(report["results"]) == 2
    cancelled_row = report["results"][1]
    assert cancelled_row["date"] is None
    assert cancelled_row["time"] is None
    assert "학생 휴강 요청" in cancelled_row["remarks"]
