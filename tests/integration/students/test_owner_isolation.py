"""FR-STU-01, NFR-04: owner isolation."""

from students.models import Student
from tests.factories import StudentFactory


def test_student_queryset_filtered_by_owner(user, other_user):
    mine = StudentFactory(owner=user, name="내학생")
    StudentFactory(owner=other_user, name="남학생")
    ids = list(Student.objects.filter(owner=user).values_list("id", flat=True))
    assert ids == [mine.id]
