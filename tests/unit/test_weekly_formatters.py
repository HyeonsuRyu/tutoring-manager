"""FR-RPT-05, FR-RPT-06: weekly remarks and 60-minute highlight (no DB)."""

from datetime import date, datetime, timezone as dt_timezone
from types import SimpleNamespace

from core.weekly_formatters import (
    format_cancelled_remarks,
    format_completed_remarks,
    time_should_highlight,
)


def _lesson(**kwargs):
    defaults = {
        "status": "cancelled",
        "cancelled_by": "student",
        "cancel_reason": "",
        "makeup_status": "no_makeup",
        "makeup_date": None,
        "lesson_notes": "",
        "lesson_content": "",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_cancelled_student_no_reason_fixed_phrase():
    lesson = _lesson(cancelled_by="student", cancel_reason="", makeup_status="no_makeup")
    assert format_cancelled_remarks(lesson) == (
        "학생 휴강 요청, 사유 전달 받지 못함 / 보강 예정 없음"
    )


def test_cancelled_teacher_with_reason():
    lesson = _lesson(
        cancelled_by="teacher",
        cancel_reason="개인 사정",
        makeup_status="undecided",
    )
    remarks = format_cancelled_remarks(lesson)
    assert "개인 사정" in remarks
    assert "휴강" in remarks
    assert " / " in remarks


def test_cancelled_makeup_scheduled():
    lesson = _lesson(
        cancelled_by="student",
        cancel_reason="가족 행사",
        makeup_status="scheduled",
        makeup_date=date(2026, 5, 28),
    )
    assert "05월 28일 보강 예정" in format_cancelled_remarks(lesson)


def test_completed_remarks_prefers_notes():
    lesson = _lesson(status="completed", lesson_notes="숙제 확인", lesson_content="단원1")
    assert format_completed_remarks(lesson) == "숙제 확인"


def test_time_highlight_when_not_60_minutes():
    start = datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc)
    end = datetime(2026, 3, 18, 11, 30, tzinfo=dt_timezone.utc)
    assert time_should_highlight(start, end) is True


def test_time_no_highlight_for_60_minutes():
    start = datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc)
    end = datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc)
    assert time_should_highlight(start, end) is False
