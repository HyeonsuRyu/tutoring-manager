"""Completed lessons cannot be edited until uncompleted."""

from datetime import date, datetime, timezone as dt_timezone

import pytest
from django.contrib.messages import get_messages

from calendar_app.models import Lesson
from tests.factories import LessonFactory


@pytest.mark.integration
def test_completed_lesson_update_rejected(logged_in_client, student):
    lesson = LessonFactory(
        student=student,
        status=Lesson.Status.COMPLETED,
        date=date(2026, 3, 18),
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
        lesson_content="원본",
    )
    res = logged_in_client.post(
        f"/students/{student.pk}/?lesson={lesson.pk}",
        {
            "action": "lesson_update",
            "lesson_id": str(lesson.pk),
            "lesson_date": "2026-03-19",
            "start_time": "14:00",
            "end_time": "15:00",
            "lesson_content": "변경 시도",
            "lesson_notes": "",
        },
        follow=True,
    )
    assert res.status_code == 200
    lesson.refresh_from_db()
    assert lesson.lesson_content == "원본"
    assert lesson.date.isoformat() == "2026-03-18"
    msgs = [str(m) for m in get_messages(res.wsgi_request)]
    assert any("완료된 수업" in m for m in msgs)
