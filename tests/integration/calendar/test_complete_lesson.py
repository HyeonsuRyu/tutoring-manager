"""FR-CAL-08: complete lesson increments lessons_completed once."""

from calendar_app.services import complete_lesson
from tests.factories import LessonFactory, StudentFactory


def test_complete_increments_once(user):
    student = StudentFactory(owner=user, lessons_completed=0)
    lesson = LessonFactory(student=student, status="scheduled")
    complete_lesson(lesson)
    student.refresh_from_db()
    assert student.lessons_completed == 1
    complete_lesson(lesson)
    student.refresh_from_db()
    assert student.lessons_completed == 1
