"""FR-RPT-07, CAL-08: web lesson complete and cancel from student detail."""

from datetime import datetime, timezone as dt_timezone

import pytest

from calendar_app.models import Lesson
from tests.factories import LessonFactory


@pytest.mark.integration
def test_complete_lesson_from_student_detail(logged_in_client, student):
    lesson = LessonFactory(
        student=student,
        status=Lesson.Status.SCHEDULED,
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
    )
    before = student.lessons_completed
    res = logged_in_client.post(f"/lessons/{lesson.pk}/complete/", {})
    assert res.status_code in (200, 302)
    student.refresh_from_db()
    lesson.refresh_from_db()
    assert lesson.status == Lesson.Status.COMPLETED
    assert student.lessons_completed == before + 1


@pytest.mark.integration
def test_cancel_lesson_from_student_detail(logged_in_client, student):
    lesson = LessonFactory(student=student, status=Lesson.Status.SCHEDULED)
    res = logged_in_client.post(
        f"/lessons/{lesson.pk}/cancel/",
        {
            "cancelled_by": "teacher",
            "cancel_reason": "선생님 일정",
            "makeup_status": "undecided",
        },
    )
    assert res.status_code in (200, 302)
    lesson.refresh_from_db()
    assert lesson.status == Lesson.Status.CANCELLED
