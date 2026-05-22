"""FR-CAL-13: lesson end = start + student lesson duration."""

from datetime import datetime, timezone as dt_timezone

import pytest

from calendar_app.services import _lesson_end
from tests.factories import StudentFactory


@pytest.mark.integration
def test_lesson_end_uses_student_duration():
    student = StudentFactory(lesson_duration_minutes=90)
    start = datetime(2026, 3, 18, 10, 0, tzinfo=dt_timezone.utc)
    end = _lesson_end(start, student)
    assert int((end - start).total_seconds()) == 90 * 60
