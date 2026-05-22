"""FR-CAL-04, CAL-12, CAL-14, RPT-07: lesson API approve, dismiss, cancel, patch."""

from datetime import date, datetime, timedelta, timezone as dt_timezone

import pytest

from calendar_app.models import Lesson
from tests.factories import LessonFactory


@pytest.mark.integration
@pytest.mark.api
def test_approve_proposal_creates_lesson(jwt_api_client, schedule_slot):
    res = jwt_api_client.post(
        "/api/v1/lessons/",
        {"schedule_slot_id": schedule_slot.id, "date": "2026-03-16"},
        format="json",
    )
    assert res.status_code == 201, res.content
    assert Lesson.objects.filter(schedule_slot=schedule_slot, date=date(2026, 3, 16)).exists()


@pytest.mark.integration
@pytest.mark.api
def test_dismiss_proposal(jwt_api_client, schedule_slot):
    res = jwt_api_client.post(
        "/api/v1/proposals/dismiss/",
        {"schedule_slot_id": schedule_slot.id, "date": "2026-03-16"},
        format="json",
    )
    assert res.status_code == 201, res.content


@pytest.mark.integration
@pytest.mark.api
def test_cancel_lesson_api(jwt_api_client, student):
    lesson = LessonFactory(
        student=student,
        status=Lesson.Status.SCHEDULED,
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
    )
    res = jwt_api_client.post(
        f"/api/v1/lessons/{lesson.id}/cancel/",
        {
            "cancelled_by": "student",
            "cancel_reason": "개인 사정",
            "makeup_status": "scheduled",
            "makeup_date": "2026-03-25",
        },
        format="json",
    )
    assert res.status_code == 200, res.content
    lesson.refresh_from_db()
    assert lesson.status == Lesson.Status.CANCELLED
    assert lesson.cancel_reason == "개인 사정"


@pytest.mark.integration
@pytest.mark.api
def test_patch_reschedule_lesson(jwt_api_client, student):
    lesson = LessonFactory(
        student=student,
        status=Lesson.Status.SCHEDULED,
        start_datetime=datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc),
        end_datetime=datetime(2026, 3, 18, 11, 0, tzinfo=dt_timezone.utc),
    )
    new_start = datetime(2026, 3, 18, 14, 0, tzinfo=dt_timezone.utc)
    new_end = datetime(2026, 3, 18, 15, 30, tzinfo=dt_timezone.utc)
    res = jwt_api_client.patch(
        f"/api/v1/lessons/{lesson.id}/",
        {"start_datetime": new_start.isoformat(), "end_datetime": new_end.isoformat()},
        format="json",
    )
    assert res.status_code == 200, res.content
    lesson.refresh_from_db()
    assert lesson.start_datetime == new_start


@pytest.mark.integration
@pytest.mark.api
def test_patch_lesson_content_notes(jwt_api_client, student):
    lesson = LessonFactory(student=student, status=Lesson.Status.SCHEDULED)
    res = jwt_api_client.patch(
        f"/api/v1/lessons/{lesson.id}/",
        {"lesson_content": "단원 3", "lesson_notes": "숙제 확인"},
        format="json",
    )
    assert res.status_code == 200, res.content
    lesson.refresh_from_db()
    assert lesson.lesson_content == "단원 3"
    assert lesson.lesson_notes == "숙제 확인"


@pytest.mark.integration
@pytest.mark.api
def test_completed_lesson_start_unchanged_on_reschedule_attempt(jwt_api_client, student):
    lesson = LessonFactory(student=student, status=Lesson.Status.COMPLETED)
    old_start = lesson.start_datetime
    new_start = (lesson.start_datetime + timedelta(hours=2)).isoformat()
    res = jwt_api_client.patch(
        f"/api/v1/lessons/{lesson.id}/",
        {"start_datetime": new_start},
        format="json",
    )
    assert res.status_code == 400
    lesson.refresh_from_db()
    assert lesson.status == Lesson.Status.COMPLETED
    assert lesson.start_datetime == old_start
