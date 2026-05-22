"""FR-STU-02, FR-STU-11: student fields and next lesson number."""

from tests.factories import StudentFactory


def test_next_lesson_number_is_completed_plus_one():
    student = StudentFactory(lessons_completed=5)
    assert student.next_lesson_number == 6


def test_age_from_birth_year():
    student = StudentFactory(birth_year=2010)
    assert student.age >= 15
