"""Korean grade ↔ birth year helpers."""

from datetime import date

from core.grade_suggest import birth_year_to_grade, grade_to_birth_year


def test_birth_year_2008_is_high_school_senior():
    assert birth_year_to_grade(2008, today=date(2026, 5, 1)) == "고3"


def test_birth_year_to_grade_middle_school():
    assert birth_year_to_grade(2012, today=date(2026, 5, 1)) == "중2"


def test_grade_to_birth_year():
    assert grade_to_birth_year("고3", today=date(2026, 5, 1)) == 2008


def test_roundtrip_primary():
    by = grade_to_birth_year("초3", today=date(2026, 9, 1))
    assert birth_year_to_grade(by, today=date(2026, 9, 1)) == "초3"
