"""FR-STU-*: Students REST API (HTTP)."""

from tests.factories import StudentFactory


def test_list_students(jwt_api_client, student):
    res = jwt_api_client.get("/api/v1/students/")
    assert res.status_code == 200, res.content
    data = res.json()
    assert "results" in data
    assert any(r["name"] == "김학생" for r in data["results"])


def test_retrieve_student(jwt_api_client, student):
    res = jwt_api_client.get(f"/api/v1/students/{student.id}/")
    assert res.status_code == 200
    assert res.json()["next_lesson_number"] == student.lessons_completed + 1


def test_cannot_access_other_users_student(jwt_api_client, other_user):
    other_student = StudentFactory(owner=other_user)
    res = jwt_api_client.get(f"/api/v1/students/{other_student.id}/")
    assert res.status_code == 404
