"""FR-RPT-07, CAL-08: web lesson complete and cancel from student detail."""

from datetime import datetime, timedelta, timezone as dt_timezone

import pytest
from django.contrib.messages import get_messages
from django.utils import timezone

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
def test_complete_lesson_saves_content_and_notes(logged_in_client, student):
    lesson = LessonFactory(
        student=student,
        status=Lesson.Status.SCHEDULED,
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
        lesson_content="",
        lesson_notes="",
    )
    res = logged_in_client.post(
        f"/lessons/{lesson.pk}/complete/",
        {"lesson_content": "단원 4", "lesson_notes": "숙제 10번"},
    )
    assert res.status_code in (200, 302)
    lesson.refresh_from_db()
    assert lesson.status == Lesson.Status.COMPLETED
    assert lesson.lesson_content == "단원 4"
    assert lesson.lesson_notes == "숙제 10번"


@pytest.mark.integration
def test_complete_lesson_before_start_rejected(logged_in_client, student):
    start = timezone.now() + timedelta(hours=2)
    lesson = LessonFactory(
        student=student,
        status=Lesson.Status.SCHEDULED,
        start_datetime=start,
        end_datetime=start + timedelta(hours=1),
    )
    before = student.lessons_completed
    res = logged_in_client.post(
        f"/lessons/{lesson.pk}/complete/",
        {},
        follow=True,
    )
    assert res.status_code == 200
    lesson.refresh_from_db()
    student.refresh_from_db()
    assert lesson.status == Lesson.Status.SCHEDULED
    assert student.lessons_completed == before
    msgs = [str(m) for m in get_messages(res.wsgi_request)]
    assert any("아직 수업 전" in m for m in msgs)


@pytest.mark.integration
def test_lesson_detail_update_schedule(logged_in_client, student):
    lesson = LessonFactory(
        student=student,
        status=Lesson.Status.SCHEDULED,
        date=__import__("datetime").date(2026, 3, 18),
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
    )
    res = logged_in_client.post(
        f"/students/{student.pk}/?lesson={lesson.pk}",
        {
            "action": "lesson_update",
            "lesson_id": str(lesson.pk),
            "lesson_date": "2026-03-19",
            "start_time": "14:00",
            "end_time": "15:30",
            "lesson_content": "복습",
            "lesson_notes": "",
        },
    )
    assert res.status_code == 302
    lesson.refresh_from_db()
    assert lesson.date.isoformat() == "2026-03-19"
    assert lesson.lesson_content == "복습"


@pytest.mark.integration
def test_uncomplete_lesson_from_detail(logged_in_client, student):
    lesson = LessonFactory(
        student=student,
        status=Lesson.Status.COMPLETED,
        completion_counted=True,
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
    )
    student.lessons_completed = 1
    student.save(update_fields=["lessons_completed", "updated_at"])
    res = logged_in_client.post(f"/lessons/{lesson.pk}/uncomplete/", {})
    assert res.status_code == 302
    lesson.refresh_from_db()
    student.refresh_from_db()
    assert lesson.status == Lesson.Status.SCHEDULED
    assert student.lessons_completed == 0
    assert lesson.completed_at is None


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
