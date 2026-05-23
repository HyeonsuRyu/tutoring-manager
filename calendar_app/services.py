"""Calendar domain logic. See docs/calendar.md."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from typing import Any
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Max
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
    course_name: str = ""
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
            "course_name": self.course_name,
            "timezone": self.timezone,
            "display_start": self.display_start,
            "display_end": self.display_end,
        }


def iter_dates(start: date, end: date):
    """Yield each day in [start, end). end is exclusive (FullCalendar convention)."""
    current = start
    while current < end:
        yield current
        current += timedelta(days=1)


def _calendar_range_bounds(range_start: date, range_end: date) -> tuple[datetime, datetime]:
    """UTC bounds for [range_start, range_end) where range_end is exclusive."""
    start_dt = django_tz.make_aware(datetime.combine(range_start, time.min))
    end_dt = django_tz.make_aware(datetime.combine(range_end, time.min))
    return start_dt, end_dt


def _localize_slot_start(student: Student, slot: ScheduleSlot, d: date) -> datetime:
    tz = ZoneInfo(student.timezone)
    naive = datetime.combine(d, slot.start_time)
    return naive.replace(tzinfo=tz).astimezone(dt_timezone.utc)


def _lesson_end(start: datetime, student: Student) -> datetime:
    return start + timedelta(minutes=student.lesson_duration_minutes)


def next_lesson_number(student: Student) -> int:
    """Next 회차 for proposals (max existing + 1)."""
    current = Lesson.objects.filter(student=student).aggregate(m=Max("lesson_number"))["m"]
    return (current or 0) + 1


def lesson_numbers_need_resequence(student: Student) -> bool:
    expected = 1
    for lesson in (
        Lesson.objects.filter(student=student)
        .order_by("date", "start_datetime", "id")
        .only("lesson_number")
    ):
        if lesson.lesson_number != expected:
            return True
        expected += 1
    return False


def resequence_students_if_needed(owner, student_ids: set[int] | list[int]) -> bool:
    """Resequence lesson numbers when out of order. Returns True if any student updated."""
    if not student_ids:
        return False
    updated = False
    for student in Student.objects.filter(pk__in=student_ids, owner=owner):
        if lesson_numbers_need_resequence(student):
            resequence_lesson_numbers(student)
            updated = True
    return updated


def resequence_lesson_numbers(student: Student) -> int:
    """Re-number all lessons for a student by date, then start_datetime (ascending)."""
    lessons = list(
        Lesson.objects.filter(student=student).order_by("date", "start_datetime", "id")
    )
    to_update: list[Lesson] = []
    for idx, lesson in enumerate(lessons, start=1):
        if lesson.lesson_number != idx:
            lesson.lesson_number = idx
            to_update.append(lesson)
    if to_update:
        Lesson.objects.bulk_update(to_update, ["lesson_number"])
    return len(to_update)


def _lesson_duration_minutes(lesson: Lesson) -> int:
    return int((lesson.end_datetime - lesson.start_datetime).total_seconds() // 60)


def _lesson_subtitle(lesson: Lesson) -> str:
    mins = _lesson_duration_minutes(lesson)
    if lesson.course_name:
        return f"{lesson.lesson_number}회차 · {lesson.course_name} · {mins}분"
    return f"{lesson.lesson_number}회차 · {mins}분"


def _display_times(student: Student, start: datetime, end: datetime) -> tuple[str, str]:
    tz = ZoneInfo(student.timezone)
    local_start = start.astimezone(tz)
    local_end = end.astimezone(tz)
    return local_start.strftime("%Y-%m-%d %H:%M"), local_end.strftime("%H:%M")


def get_lessons_for_range(owner, range_start: date, range_end: date) -> list[Lesson]:
    """Lessons overlapping the visible calendar range (range_end exclusive)."""
    start_dt, end_dt = _calendar_range_bounds(range_start, range_end)
    return list(
        Lesson.objects.filter(
            student__owner=owner,
            start_datetime__lt=end_dt,
            end_datetime__gt=start_dt,
        )
        .select_related("student")
        .order_by("start_datetime")
    )


def get_proposed_events(owner, range_start: date, range_end: date) -> list[CalendarEvent]:
    slots = ScheduleSlot.objects.filter(student__owner=owner).select_related("student")
    dismissed = {
        (d.schedule_slot_id, d.date)
        for d in LessonProposalDismissal.objects.filter(owner=owner, date__gte=range_start, date__lt=range_end)
    }
    existing = {
        (lesson.schedule_slot_id, lesson.date)
        for lesson in Lesson.objects.filter(
            student__owner=owner,
            schedule_slot__isnull=False,
            date__gte=range_start,
            date__lt=range_end,
        )
    }
    now = django_tz.now()
    candidates: list[tuple[ScheduleSlot, date, datetime, datetime]] = []
    for slot in slots:
        student = slot.student
        for d in iter_dates(range_start, range_end):
            if date_to_slot_day_of_week(d) != slot.day_of_week:
                continue
            key = (slot.id, d)
            if key in dismissed or key in existing:
                continue
            start = _localize_slot_start(student, slot, d)
            if start <= now:
                continue
            end = _lesson_end(start, student)
            candidates.append((slot, d, start, end))
    candidates.sort(key=lambda row: row[2])

    student_counters: dict[int, int] = {}
    events: list[CalendarEvent] = []
    for slot, d, start, end in candidates:
        student = slot.student
        if student.id not in student_counters:
            student_counters[student.id] = next_lesson_number(student)
        else:
            student_counters[student.id] += 1
        num = student_counters[student.id]
        duration = int((end - start).total_seconds() // 60)
        disp_start, disp_end = _display_times(student, start, end)
        events.append(
            CalendarEvent(
                id=f"proposal-{slot.id}-{d.isoformat()}",
                type="proposal",
                student_id=student.id,
                student_name=student.name,
                title=student.name,
                subtitle=f"{num}회차 · {duration}분",
                start=start,
                end=end,
                date=d,
                lesson_number=num,
                status="scheduled",
                ui_state=compute_ui_state(
                    status="scheduled", start=start, end=end, now=now, proposed=True
                ),
                proposed=True,
                duration_minutes=duration,
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
                subtitle=_lesson_subtitle(lesson),
                start=lesson.start_datetime,
                end=lesson.end_datetime,
                date=lesson.date,
                lesson_number=lesson.lesson_number,
                status=lesson.status,
                ui_state=ui,
                proposed=False,
                duration_minutes=_lesson_duration_minutes(lesson),
                schedule_slot_id=lesson.schedule_slot_id,
                lesson_content=lesson.lesson_content,
                lesson_notes=lesson.lesson_notes,
                course_name=lesson.course_name,
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
    student_ids = set(
        Lesson.objects.filter(student__owner=owner).values_list("student_id", flat=True).distinct()
    )
    if resequence_students_if_needed(owner, student_ids):
        pass
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
    existing = Lesson.objects.filter(
        student=student,
        schedule_slot=slot,
        date=on_date,
    ).first()
    if existing:
        return existing
    start = _localize_slot_start(student, slot, on_date)
    end = _lesson_end(start, student)
    lesson = Lesson.objects.create(
        student=student,
        schedule_slot=slot,
        date=on_date,
        start_datetime=start,
        end_datetime=end,
        lesson_number=1,
        status=Lesson.Status.SCHEDULED,
    )
    resequence_lesson_numbers(student)
    lesson.refresh_from_db()
    return lesson


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
    resequence_lesson_numbers(student)
    lesson.refresh_from_db()
    return lesson


def resolve_student_for_owner(
    owner,
    *,
    student_id: int | None = None,
    student_name: str = "",
) -> Student:
    if student_id is not None:
        return Student.objects.get(pk=student_id, owner=owner)
    name = student_name.strip()
    if not name:
        raise ValueError("학생 이름을 입력하세요.")
    matches = Student.objects.filter(owner=owner, name=name)
    if matches.count() == 1:
        return matches.get()
    if matches.count() == 0:
        raise ValueError(f"학생을 찾을 수 없습니다: {name}")
    raise ValueError(f"같은 이름의 학생이 여러 명입니다: {name}")


@transaction.atomic
def create_manual_lesson(
    owner,
    *,
    student: Student,
    course_name: str,
    on_date: date,
    start_time: time,
    end_time: time,
) -> Lesson:
    tz = ZoneInfo(student.timezone)
    start_local = datetime.combine(on_date, start_time)
    end_local = datetime.combine(on_date, end_time)
    if end_local <= start_local:
        raise ValueError("종료 시간은 시작 시간보다 늦어야 합니다.")
    start_dt = start_local.replace(tzinfo=tz).astimezone(dt_timezone.utc)
    end_dt = end_local.replace(tzinfo=tz).astimezone(dt_timezone.utc)
    lesson = Lesson.objects.create(
        student=student,
        schedule_slot=None,
        date=on_date,
        start_datetime=start_dt,
        end_datetime=end_dt,
        lesson_number=1,
        course_name=course_name.strip(),
        status=Lesson.Status.SCHEDULED,
    )
    resequence_lesson_numbers(student)
    lesson.refresh_from_db()
    return lesson


def materialize_due_proposals(owner, now: datetime | None = None) -> list[Lesson]:
    """Create lessons for recurring slots whose start time has passed (not shown as proposals)."""
    now = now or django_tz.now()
    today = now.date()
    window_start = today - timedelta(days=7)
    range_end = today + timedelta(days=1)
    slots = ScheduleSlot.objects.filter(student__owner=owner).select_related("student")
    dismissed = {
        (d.schedule_slot_id, d.date)
        for d in LessonProposalDismissal.objects.filter(
            owner=owner, date__gte=window_start, date__lt=range_end
        )
    }
    existing = {
        (lesson.schedule_slot_id, lesson.date)
        for lesson in Lesson.objects.filter(
            student__owner=owner,
            schedule_slot__isnull=False,
            date__gte=window_start,
            date__lt=range_end,
        )
    }
    created: list[Lesson] = []
    for slot in slots:
        student = slot.student
        for d in iter_dates(window_start, range_end):
            if date_to_slot_day_of_week(d) != slot.day_of_week:
                continue
            key = (slot.id, d)
            if key in dismissed or key in existing:
                continue
            start = _localize_slot_start(student, slot, d)
            if start > now:
                continue
            lesson = approve_proposal(owner, slot.id, d)
            created.append(lesson)
            existing.add(key)
    return created
