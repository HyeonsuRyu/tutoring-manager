"""Weekly lesson status report. See docs/weekly-lesson-status.md."""

from __future__ import annotations

from datetime import date
from typing import Any
from zoneinfo import ZoneInfo

from calendar_app.models import Lesson
from core.iso_week import iso_week_range, week_label
from core.weekly_formatters import (
    format_cancelled_remarks,
    format_completed_remarks,
    time_should_highlight,
)
from students.models import Student

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]


def _weekday_label(d: date) -> str:
    return WEEKDAY_KO[d.weekday()]


def _format_time_local(lesson: Lesson) -> str:
    tz = ZoneInfo(lesson.student.timezone)
    start = lesson.start_datetime.astimezone(tz)
    end = lesson.end_datetime.astimezone(tz)
    return f"{start:%H:%M}~{end:%H:%M}"


def get_weekly_lessons(owner, iso_year: int, iso_week: int) -> list[Lesson]:
    week_start, week_end = iso_week_range(iso_year, iso_week)
    return list(
        Lesson.objects.filter(
            student__owner=owner,
            status__in=[Lesson.Status.COMPLETED, Lesson.Status.CANCELLED],
            start_datetime__date__gte=week_start,
            start_datetime__date__lte=week_end,
        )
        .select_related("student")
        .order_by("start_datetime")
    )


def build_weekly_row(seq: int, lesson: Lesson) -> dict[str, Any]:
    student: Student = lesson.student
    if lesson.status == Lesson.Status.CANCELLED:
        return {
            "seq": seq,
            "date": None,
            "weekday": None,
            "time": None,
            "time_highlight": False,
            "course_name": lesson.course_name or "—",
            "lesson_kind_display": lesson.get_lesson_kind_display(),
            "student_name": student.name,
            "grade": student.grade,
            "remarks": format_cancelled_remarks(lesson),
            "status": lesson.status,
        }

    local_date = lesson.start_datetime.astimezone(ZoneInfo(student.timezone)).date()
    return {
        "seq": seq,
        "date": f"{local_date:%m.%d}",
        "weekday": _weekday_label(local_date),
        "time": _format_time_local(lesson),
        "time_highlight": time_should_highlight(lesson.start_datetime, lesson.end_datetime),
        "course_name": lesson.course_name or "—",
        "lesson_kind_display": lesson.get_lesson_kind_display(),
        "student_name": student.name,
        "grade": student.grade,
        "remarks": format_completed_remarks(lesson),
        "status": lesson.status,
    }


def get_weekly_report(owner, iso_year: int, iso_week: int) -> dict[str, Any]:
    week_start, week_end = iso_week_range(iso_year, iso_week)
    lessons = get_weekly_lessons(owner, iso_year, iso_week)
    results = [build_weekly_row(i + 1, lesson) for i, lesson in enumerate(lessons)]
    return {
        "year": iso_year,
        "week": iso_week,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "label": week_label(iso_week, week_start, week_end),
        "results": results,
    }


def list_week_options(iso_year: int, max_week: int = 53) -> dict[str, Any]:
    weeks = []
    for w in range(1, max_week + 1):
        try:
            start, end = iso_week_range(iso_year, w)
        except ValueError:
            break
        if start.year != iso_year and end.year != iso_year and w > 1:
            break
        if start.isocalendar()[0] != iso_year and w > 1:
            continue
        weeks.append(
            {
                "week": w,
                "label": week_label(w, start, end),
                "week_start": start.isoformat(),
                "week_end": end.isoformat(),
            }
        )
    return {"year": iso_year, "weeks": weeks}
