"""Calendar domain logic. See docs/calendar.md."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone as dt_timezone
from typing import Any
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone as django_tz

from calendar_app.models import Lesson, LessonProposalDismissal
from core.day_of_week import date_to_slot_day_of_week
from core.lesson_ui_state import compute_ui_state
from students.models import ScheduleSlot, Student


@dataclass
class CalendarEvent:
    id: str
    type: str
    student_id: int
    student_name: str
    title: str
    subtitle: str
    start: datetime
    end: datetime
    date: date
    lesson_number: int
    status: str
    ui_state: str
    proposed: bool
    duration_minutes: int
    schedule_slot_id: int | None = None
    lesson_content: str = ""
    lesson_notes: str = ""
    timezone: str = "UTC"
    display_start: str = ""
    display_end: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "title": self.title,
            "subtitle": self.subtitle,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "date": self.date.isoformat(),
            "lesson_number": self.lesson_number,
            "status": self.status,
            "ui_state": self.ui_state,
            "proposed": self.proposed,
            "duration_minutes": self.duration_minutes,
            "schedule_slot_id": self.schedule_slot_id,
            "lesson_content": self.lesson_content,
            "lesson_notes": self.lesson_notes,
            "timezone": self.timezone,
            "display_start": self.display_start,
            "display_end": self.display_end,
        }


def is_visible_on_calendar(student: Student, on_date: date) -> bool:
    """False before first_lesson_date when that field is set."""
    if student.first_lesson_date is None:
        return True
    return on_date >= student.first_lesson_date


def iter_dates(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _localize_slot_start(student: Student, slot: ScheduleSlot, d: date) -> datetime:
    tz = ZoneInfo(student.timezone)
    naive = datetime.combine(d, slot.start_time)
    return naive.replace(tzinfo=tz).astimezone(dt_timezone.utc)


def _lesson_end(start: datetime, student: Student) -> datetime:
    return start + timedelta(minutes=student.lesson_duration_minutes)


def _display_times(student: Student, start: datetime, end: datetime) -> tuple[str, str]:
    tz = ZoneInfo(student.timezone)
    local_start = start.astimezone(tz)
    local_end = end.astimezone(tz)
    return local_start.strftime("%Y-%m-%d %H:%M"), local_end.strftime("%H:%M")


def get_lessons_for_range(owner, range_start: date, range_end: date) -> list[Lesson]:
    return list(
        Lesson.objects.filter(
            student__owner=owner,
            date__gte=range_start,
            date__lte=range_end,
        )
        .filter(
            Q(student__first_lesson_date__isnull=True)
            | Q(date__gte=F("student__first_lesson_date"))
        )
        .select_related("student")
        .order_by("start_datetime")
    )


def get_proposed_events(owner, range_start: date, range_end: date) -> list[CalendarEvent]:
    slots = ScheduleSlot.objects.filter(student__owner=owner).select_related("student")
    dismissed = {
        (d.schedule_slot_id, d.date)
        for d in LessonProposalDismissal.objects.filter(owner=owner, date__gte=range_start, date__lte=range_end)
    }
    existing = {
        (lesson.schedule_slot_id, lesson.date)
        for lesson in Lesson.objects.filter(
            student__owner=owner,
            schedule_slot__isnull=False,
            date__gte=range_start,
            date__lte=range_end,
        )
    }
    events: list[CalendarEvent] = []
    now = django_tz.now()
    for slot in slots:
        student = slot.student
        for d in iter_dates(range_start, range_end):
            if not is_visible_on_calendar(student, d):
                continue
            if date_to_slot_day_of_week(d) != slot.day_of_week:
                continue
            key = (slot.id, d)
            if key in dismissed or key in existing:
                continue
            start = _localize_slot_start(student, slot, d)
            end = _lesson_end(start, student)
            num = student.lessons_completed + 1
            disp_start, disp_end = _display_times(student, start, end)
            events.append(
                CalendarEvent(
                    id=f"proposal-{slot.id}-{d.isoformat()}",
                    type="proposal",
                    student_id=student.id,
                    student_name=student.name,
                    title=student.name,
                    subtitle=f"{num}회차 · {student.lesson_duration_minutes}분",
                    start=start,
                    end=end,
                    date=d,
                    lesson_number=num,
                    status="scheduled",
                    ui_state=compute_ui_state(
                        status="scheduled", start=start, end=end, now=now, proposed=True
                    ),
                    proposed=True,
                    duration_minutes=student.lesson_duration_minutes,
                    schedule_slot_id=slot.id,
                    timezone=student.timezone,
                    display_start=disp_start,
                    display_end=disp_end,
                )
            )
    return events


def lessons_to_events(lessons: list[Lesson], now: datetime | None = None) -> list[CalendarEvent]:
    now = now or django_tz.now()
    events = []
    for lesson in lessons:
        student = lesson.student
        ui = compute_ui_state(
            status=lesson.status,
            start=lesson.start_datetime,
            end=lesson.end_datetime,
            now=now,
        )
        disp_start, disp_end = _display_times(student, lesson.start_datetime, lesson.end_datetime)
        events.append(
            CalendarEvent(
                id=f"lesson-{lesson.id}",
                type="lesson",
                student_id=student.id,
                student_name=student.name,
                title=student.name,
                subtitle=f"{lesson.lesson_number}회차 · {student.lesson_duration_minutes}분",
                start=lesson.start_datetime,
                end=lesson.end_datetime,
                date=lesson.date,
                lesson_number=lesson.lesson_number,
                status=lesson.status,
                ui_state=ui,
                proposed=False,
                duration_minutes=int((lesson.end_datetime - lesson.start_datetime).total_seconds() // 60),
                schedule_slot_id=lesson.schedule_slot_id,
                lesson_content=lesson.lesson_content,
                lesson_notes=lesson.lesson_notes,
                timezone=student.timezone,
                display_start=disp_start,
                display_end=disp_end,
            )
        )
    return events


def find_conflicts(events: list[CalendarEvent]) -> list[dict[str, Any]]:
    """Overlapping intervals among lesson/proposal events."""
    sorted_events = sorted(events, key=lambda e: e.start)
    conflicts: list[dict[str, Any]] = []
    for i, a in enumerate(sorted_events):
        for b in sorted_events[i + 1 :]:
            if b.start >= a.end:
                break
            if a.end > b.start:
                conflicts.append(
                    {
                        "event_ids": [a.id, b.id],
                        "message": "겹치는 수업",
                    }
                )
    return conflicts


def get_calendar_events(owner, range_start: date, range_end: date, *, materialize: bool = True) -> dict[str, Any]:
    if materialize:
        materialize_due_proposals(owner)
    lessons = get_lessons_for_range(owner, range_start, range_end)
    lesson_events = lessons_to_events(lessons)
    proposed = get_proposed_events(owner, range_start, range_end)
    all_events = lesson_events + proposed
    conflicts = find_conflicts(all_events)
    conflict_ids: set[str] = set()
    for c in conflicts:
        conflict_ids.update(c["event_ids"])
    event_dicts = []
    for e in all_events:
        d = e.to_dict()
        d["has_conflict"] = e.id in conflict_ids
        event_dicts.append(d)
    return {
        "events": event_dicts,
        "conflicts": conflicts,
    }


@transaction.atomic
def approve_proposal(owner, schedule_slot_id: int, on_date: date) -> Lesson:
    slot = ScheduleSlot.objects.select_related("student").get(
        id=schedule_slot_id, student__owner=owner
    )
    student = slot.student
    if not is_visible_on_calendar(student, on_date):
        raise ValueError("Cannot approve a lesson before the student's first lesson date.")
    start = _localize_slot_start(student, slot, on_date)
    end = _lesson_end(start, student)
    return Lesson.objects.create(
        student=student,
        schedule_slot=slot,
        date=on_date,
        start_datetime=start,
        end_datetime=end,
        lesson_number=student.lessons_completed + 1,
        status=Lesson.Status.SCHEDULED,
    )


def dismiss_proposal(owner, schedule_slot_id: int, on_date: date) -> LessonProposalDismissal:
    slot = ScheduleSlot.objects.get(id=schedule_slot_id, student__owner=owner)
    dismissal, _ = LessonProposalDismissal.objects.get_or_create(
        owner=owner, schedule_slot=slot, date=on_date
    )
    return dismissal


class LessonNotStartedError(ValueError):
    """Raised when completing a lesson before its scheduled start time."""


def update_lesson_content(
    lesson: Lesson,
    *,
    lesson_content: str = "",
    lesson_notes: str = "",
) -> Lesson:
    lesson.lesson_content = lesson_content
    lesson.lesson_notes = lesson_notes
    lesson.save(update_fields=["lesson_content", "lesson_notes"])
    return lesson


def lesson_has_started(lesson: Lesson, now: datetime | None = None) -> bool:
    now = now or django_tz.now()
    return now >= lesson.start_datetime


@transaction.atomic
def complete_lesson(lesson: Lesson, now: datetime | None = None) -> Lesson:
    now = now or django_tz.now()
    if not lesson_has_started(lesson, now):
        raise LessonNotStartedError()
    if lesson.status == Lesson.Status.COMPLETED and lesson.completion_counted:
        return lesson
    lesson.status = Lesson.Status.COMPLETED
    lesson.completed_at = django_tz.now()
    if not lesson.completion_counted:
        student = lesson.student
        student.lessons_completed += 1
        student.save(update_fields=["lessons_completed", "updated_at"])
        lesson.completion_counted = True
    lesson.save()
    return lesson


@transaction.atomic
def cancel_lesson(
    lesson: Lesson,
    *,
    cancelled_by: str,
    cancel_reason: str = "",
    makeup_status: str = "undecided",
    makeup_date: date | None = None,
) -> Lesson:
    lesson.status = Lesson.Status.CANCELLED
    lesson.cancelled_by = cancelled_by
    lesson.cancel_reason = cancel_reason
    lesson.makeup_status = makeup_status
    lesson.makeup_date = makeup_date
    lesson.save()
    return lesson


@transaction.atomic
def reschedule_lesson(
    lesson: Lesson,
    *,
    start_datetime: datetime,
    end_datetime: datetime | None = None,
) -> Lesson:
    if lesson.status == Lesson.Status.COMPLETED:
        raise ValueError("Completed lessons cannot be rescheduled")
    student = lesson.student
    old_date = lesson.date
    if end_datetime is None:
        duration = lesson.end_datetime - lesson.start_datetime
        end_datetime = start_datetime + duration
    new_date = start_datetime.astimezone(ZoneInfo(student.timezone)).date()
    lesson.start_datetime = start_datetime
    lesson.end_datetime = end_datetime
    lesson.date = new_date
    lesson.save(
        update_fields=["start_datetime", "end_datetime", "date"]
    )
    if lesson.schedule_slot_id and old_date != new_date:
        dismiss_proposal(student.owner, lesson.schedule_slot_id, old_date)
    return lesson


def materialize_due_proposals(owner, now: datetime | None = None) -> list[Lesson]:
    """Create lessons for proposals whose start time has passed."""
    now = now or django_tz.now()
    today = now.date()
    window_start = today - timedelta(days=7)
    proposed = get_proposed_events(owner, window_start, today + timedelta(days=14))
    created: list[Lesson] = []
    for event in proposed:
        if event.start <= now and event.schedule_slot_id:
            lesson = approve_proposal(owner, event.schedule_slot_id, event.date)
            created.append(lesson)
    return created
