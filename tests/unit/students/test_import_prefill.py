"""Progress import → student registration prefill."""

from datetime import date

import pytest

from students.import_prefill import build_student_prefill, korean_age_to_birth_year


@pytest.mark.unit
def test_korean_age_to_birth_year():
    assert korean_age_to_birth_year(17, today=date(2026, 5, 22)) == 2010
    assert korean_age_to_birth_year(0) is None
    assert korean_age_to_birth_year(200) is None


@pytest.mark.django_db
@pytest.mark.unit
def test_build_student_prefill(django_user_model):
    user = django_user_model.objects.create_user(
        username="prefill@test.com",
        email="prefill@test.com",
        password="x",
    )
    prefill = build_student_prefill(
        {
            "age": 17,
            "student_name": "홍길동",
            "teacher_name": "김선생",
            "subject": "수학",
        },
        user,
    )
    assert prefill["student_fields"]["name"] == "홍길동"
    assert prefill["student_fields"]["birth_year"] == date.today().year - 17 + 1
    assert prefill["student_fields"]["grade"]
    assert prefill["subject_ids"]
    assert "담당 교사: 김선생" in prefill["detail_memo"]
    assert "이름" in prefill["labels"]
