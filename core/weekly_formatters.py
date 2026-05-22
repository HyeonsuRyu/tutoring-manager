"""Weekly report remarks and time display. See docs/weekly-lesson-status.md."""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from calendar_app.models import Lesson

CANCELLED_BY_LABEL = {"student": "학생", "teacher": "교사"}
MAKEUP_PHRASES = {
    "undecided": "보강 일자 미정",
    "no_makeup": "보강 예정 없음",
}


def absence_label(cancelled_by: str) -> str:
    return "휴강" if cancelled_by == "teacher" else "결석"


def format_cancelled_remarks(lesson: "Lesson") -> str:
    if lesson.cancelled_by == "student" and not (lesson.cancel_reason or "").strip():
        front = "학생 휴강 요청, 사유 전달 받지 못함"
    else:
        by_label = CANCELLED_BY_LABEL.get(lesson.cancelled_by or "", "")
        reason = (lesson.cancel_reason or "").strip()
        front = f"{by_label} {reason}로 인한 {absence_label(lesson.cancelled_by or '')}".strip()

    makeup = MAKEUP_PHRASES.get(lesson.makeup_status or "undecided", MAKEUP_PHRASES["undecided"])
    if lesson.makeup_status == "scheduled" and lesson.makeup_date:
        makeup = f"{lesson.makeup_date:%m월 %d일} 보강 예정"

    return f"{front} / {makeup}"


def format_completed_remarks(lesson: "Lesson") -> str:
    if (lesson.lesson_notes or "").strip():
        return lesson.lesson_notes.strip()
    if (lesson.lesson_content or "").strip():
        return lesson.lesson_content.strip()[:80]
    return "—"


def duration_minutes(start: datetime, end: datetime) -> int:
    return max(0, int((end - start).total_seconds() // 60))


def time_should_highlight(start: datetime, end: datetime) -> bool:
    return duration_minutes(start, end) != 60
