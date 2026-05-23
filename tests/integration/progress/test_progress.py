"""FR-PRG-01~03: lesson notes and progress chart."""

from datetime import date, datetime, timezone as dt_timezone

import pytest

from calendar_app.models import Lesson
from tests.factories import LessonFactory


@pytest.mark.integration
def test_lesson_edit_via_student_detail_query(logged_in_client, student):
    lesson = LessonFactory(
        student=student,
        status=Lesson.Status.SCHEDULED,
        lesson_number=3,
    )
    res = logged_in_client.post(
        f"/students/{student.pk}/?lesson={lesson.pk}",
        {
            "action": "lesson_update",
            "lesson_id": lesson.pk,
            "lesson_content": "2단원",
            "lesson_notes": "복습",
        },
    )
    assert res.status_code == 302
    lesson.refresh_from_db()
    assert lesson.lesson_content == "2단원"
    assert lesson.lesson_notes == "복습"


@pytest.mark.integration
def test_progress_lists_completed_lesson_columns(logged_in_client, student):
    LessonFactory(
        student=student,
        status=Lesson.Status.COMPLETED,
        lesson_number=1,
        date=date(2026, 3, 18),
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
        lesson_content="완료 내용",
        lesson_notes="비고",
    )
    res = logged_in_client.get(f"/students/progress/{student.pk}/")
    body = res.content.decode()
    assert res.status_code == 200
    assert "완료 내용" in body
    assert "요일" in body or "회차" in body
    assert "progress-chart-table" in body
