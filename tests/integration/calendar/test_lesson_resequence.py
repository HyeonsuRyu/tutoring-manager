"""Lesson numbers follow chronological order per student."""

from datetime import date, datetime, time, timedelta, timezone as dt_timezone

import pytest
from freezegun import freeze_time

from calendar_app.models import Lesson
from calendar_app.services import (
    approve_proposal,
    create_manual_lesson,
    get_calendar_events,
    next_lesson_number,
    resequence_lesson_numbers,
    reschedule_lesson,
)
from tests.factories import LessonFactory, StudentFactory


@pytest.mark.integration
def test_resequence_orders_by_date_and_time(user):
    student = StudentFactory(owner=user, lessons_completed=0)
    tz = dt_timezone.utc
    l2 = LessonFactory(
        student=student,
        date=date(2026, 4, 10),
        start_datetime=datetime(2026, 4, 10, 14, 0, tzinfo=tz),
        end_datetime=datetime(2026, 4, 10, 15, 0, tzinfo=tz),
        lesson_number=99,
    )
    l1 = LessonFactory(
        student=student,
        date=date(2026, 4, 1),
        start_datetime=datetime(2026, 4, 1, 10, 0, tzinfo=tz),
        end_datetime=datetime(2026, 4, 1, 11, 0, tzinfo=tz),
        lesson_number=88,
    )
    resequence_lesson_numbers(student)
    l1.refresh_from_db()
    l2.refresh_from_db()
    assert l1.lesson_number == 1
    assert l2.lesson_number == 2


@pytest.mark.integration
@freeze_time("2026-03-15 10:00:00", tz_offset=0)
def test_reschedule_renumbers_siblings(user, student, schedule_slot):
    first = approve_proposal(user, schedule_slot.id, date(2026, 3, 16))
    second = approve_proposal(user, schedule_slot.id, date(2026, 3, 23))
    assert first.lesson_number == 1
    assert second.lesson_number == 2
    reschedule_lesson(first, start_datetime=second.start_datetime + timedelta(days=7))
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.lesson_number == 2
    assert second.lesson_number == 1


@pytest.mark.integration
def test_next_lesson_number_after_lessons(user):
    student = StudentFactory(owner=user, lessons_completed=5)
    LessonFactory(student=student, lesson_number=3)
    LessonFactory(student=student, lesson_number=7)
    assert next_lesson_number(student) == 8


@pytest.mark.integration
def test_manual_create_and_resequence(user):
    student = StudentFactory(owner=user, timezone="UTC")
    lesson = create_manual_lesson(
        user,
        student=student,
        course_name="중간고사",
        on_date=date(2026, 5, 10),
        start_time=time(10, 0),
        end_time=time(11, 30),
    )
    assert lesson.lesson_number == 1
    assert lesson.course_name == "중간고사"
    assert (lesson.end_datetime - lesson.start_datetime).total_seconds() == 90 * 60


@pytest.mark.integration
def test_calendar_load_fixes_stale_lesson_numbers(user):
    student = StudentFactory(owner=user, timezone="UTC")
    tz = dt_timezone.utc
    LessonFactory(
        student=student,
        date=date(2026, 4, 1),
        start_datetime=datetime(2026, 4, 1, 10, 0, tzinfo=tz),
        end_datetime=datetime(2026, 4, 1, 11, 0, tzinfo=tz),
        lesson_number=1,
    )
    LessonFactory(
        student=student,
        date=date(2026, 4, 10),
        start_datetime=datetime(2026, 4, 10, 10, 0, tzinfo=tz),
        end_datetime=datetime(2026, 4, 10, 11, 0, tzinfo=tz),
        lesson_number=1,
    )
    data = get_calendar_events(user, date(2026, 4, 1), date(2026, 5, 1), materialize=False)
    numbers = sorted(
        e["lesson_number"] for e in data["events"] if e["id"].startswith("lesson-")
    )
    assert numbers == [1, 2]


@pytest.mark.integration
def test_manual_create_web(logged_in_client, user):
    student = StudentFactory(owner=user, name="달력학생", timezone="UTC")
    res = logged_in_client.post(
        "/lessons/create/",
        {
            "date": "2026-06-01",
            "student_id": str(student.id),
            "student_name": student.name,
            "course_name": "문법",
            "start_time": "14:00",
            "end_time": "15:00",
        },
    )
    assert res.status_code == 200, res.content
    lesson = Lesson.objects.get(student=student, date=date(2026, 6, 1))
    assert lesson.course_name == "문법"
    assert lesson.lesson_number == 1
