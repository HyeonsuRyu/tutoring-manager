"""FR-STU-09: student detail API (memo)."""

import pytest

from students.models import StudentDetail


@pytest.mark.integration
@pytest.mark.api
def test_student_detail_get_and_patch_memo(jwt_api_client, student):
    StudentDetail.objects.get_or_create(student=student)
    res = jwt_api_client.get(f"/api/v1/students/{student.id}/detail/")
    assert res.status_code == 200
    res = jwt_api_client.patch(
        f"/api/v1/students/{student.id}/detail/",
        {"long_memo": "긴 메모 테스트"},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["long_memo"] == "긴 메모 테스트"
