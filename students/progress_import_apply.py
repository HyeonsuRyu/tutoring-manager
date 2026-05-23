"""Apply reviewed progress import rows to the database."""

from __future__ import annotations

from datetime import date, datetime, time, timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone as django_tz

from calendar_app.models import Lesson
from calendar_app.services import resequence_lesson_numbers
from students.models import Student


def _parse_time(text: str) -> time | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%H:%M").time()
    except ValueError:
        return None


def _lesson_datetimes(
    student: Student, on_date: date, start_time: time, end_time: time
) -> tuple[datetime, datetime]:
    tz = ZoneInfo(student.timezone)
    start_local = datetime.combine(on_date, start_time).replace(tzinfo=tz)
    end_local = datetime.combine(on_date, end_time).replace(tzinfo=tz)
    return (
        start_local.astimezone(dt_timezone.utc),
        end_local.astimezone(dt_timezone.utc),
    )


def validate_import_row(row: dict) -> str | None:
    """Return an error message if the row cannot be applied."""
    try:
        date.fromisoformat(row["date"])
    except (TypeError, ValueError):
        return "날짜를 입력해 주세요."
    start_time = _parse_time(row.get("start_time") or "")
    end_time = _parse_time(row.get("end_time") or "")
    if not start_time or not end_time:
        return "시간은 19:00~20:30 형식으로 입력해 주세요."
    if not (row.get("lesson_content") or "").strip():
        return "수업 내용을 입력해 주세요."
    return None


@transaction.atomic
def apply_progress_import(
    student: Student,
    rows: list[dict],
    *,
    course_name: str = "",
) -> int:
    """Create completed lessons from reviewed import rows. Returns count created."""
    course = (course_name or "").strip()
    now = django_tz.now()
    created: list[Lesson] = []
    for row in rows:
        err = validate_import_row(row)
        if err:
            raise ValueError(err)
        on_date = date.fromisoformat(row["date"])
        start_time = _parse_time(row.get("start_time") or "")
        end_time = _parse_time(row.get("end_time") or "")
        if not start_time or not end_time:
            raise ValueError("시간 형식이 올바르지 않습니다.")
        start_dt, end_dt = _lesson_datetimes(student, on_date, start_time, end_time)
        lesson = Lesson.objects.create(
            student=student,
            schedule_slot=None,
            date=on_date,
            start_datetime=start_dt,
            end_datetime=end_dt,
            lesson_number=1,
            status=Lesson.Status.COMPLETED,
            completed_at=now,
            completion_counted=False,
            lesson_content=(row.get("lesson_content") or "").strip(),
            lesson_notes=(row.get("lesson_notes") or "").strip(),
            course_name=course,
        )
        created.append(lesson)
    if not created:
        return 0
    resequence_lesson_numbers(student)
    completed_qs = Lesson.objects.filter(student=student, status=Lesson.Status.COMPLETED)
    student.lessons_completed = completed_qs.count()
    student.save(update_fields=["lessons_completed", "updated_at"])
    completed_qs.update(completion_counted=True)
    return len(created)
