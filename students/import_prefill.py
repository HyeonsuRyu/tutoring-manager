"""Build student registration initial values from progress import Excel metadata."""

from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model

from core.grade_suggest import birth_year_to_grade
from students.models import Subject

User = get_user_model()


def korean_age_to_birth_year(korean_age: int, today: date | None = None) -> int | None:
    """한국식 세는 나이 → 출생 연도 (만 나이 + 1 기준, 1월 1일 갱신)."""
    if korean_age < 1 or korean_age > 120:
        return None
    today = today or date.today()
    return today.year - korean_age + 1


def ensure_subject_for_owner(owner: User, name: str) -> Subject | None:
    subject_name = (name or "").strip()
    if not subject_name:
        return None
    subject, _created = Subject.objects.get_or_create(owner=owner, name=subject_name)
    return subject


def build_student_prefill(meta: dict, owner: User) -> dict:
    """
    Return dict with keys:
      student_fields: dict for StudentForm initial
      subject_ids: list[int] for subjects M2M
      detail_memo: str for StudentDetailForm
      labels: list[str] human-readable applied fields
    """
    meta = meta or {}
    student_fields: dict = {}
    labels: list[str] = []
    detail_lines: list[str] = []

    name = (meta.get("student_name") or "").strip()
    if name:
        student_fields["name"] = name
        labels.append("이름")

    age = meta.get("age")
    if isinstance(age, int) and age > 0:
        birth_year = korean_age_to_birth_year(age)
        if birth_year:
            student_fields["birth_year"] = birth_year
            labels.append("출생 연도(나이 환산)")
            grade = birth_year_to_grade(birth_year)
            if grade:
                student_fields["grade"] = grade
                labels.append("학년(추천)")

    teacher = (meta.get("teacher_name") or "").strip()
    if teacher:
        detail_lines.append(f"담당 교사: {teacher}")
        labels.append("메모(교사)")

    subject_ids: list[int] = []
    subject_name = (meta.get("subject") or "").strip()
    if subject_name:
        subject = ensure_subject_for_owner(owner, subject_name)
        if subject:
            subject_ids = [subject.pk]
            labels.append("과목")

    return {
        "student_fields": student_fields,
        "subject_ids": subject_ids,
        "detail_memo": "\n".join(detail_lines),
        "labels": labels,
    }
