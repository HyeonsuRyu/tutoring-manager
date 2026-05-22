"""FR-STU-02, STU-07: student create and sort via API."""

import pytest

from students.models import Student


@pytest.mark.integration
@pytest.mark.api
def test_create_student_via_api(jwt_api_client, user):
    res = jwt_api_client.post(
        "/api/v1/students/",
        {
            "name": "API학생",
            "birth_year": 2012,
            "grade": "중2",
            "timezone": "Asia/Seoul",
            "lesson_duration_minutes": 60,
            "lessons_completed": 0,
        },
        format="json",
    )
    assert res.status_code == 201, res.content
    assert Student.objects.filter(owner=user, name="API학생").exists()


@pytest.mark.integration
@pytest.mark.api
def test_list_students_sort_grade(jwt_api_client, user):
    Student.objects.create(owner=user, name="가", grade="고1", birth_year=2010)
    Student.objects.create(owner=user, name="나", grade="중1", birth_year=2011)
    res = jwt_api_client.get("/api/v1/students/", {"sort": "grade"})
    assert res.status_code == 200
    grades = [r["grade"] for r in res.json()["results"]]
    assert grades == sorted(grades, key=lambda g: (g,))
