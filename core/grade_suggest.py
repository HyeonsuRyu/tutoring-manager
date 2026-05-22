"""Korean school grade ↔ birth year helpers (March school-year baseline)."""

from __future__ import annotations

import re
from datetime import date

GRADE_PATTERN = re.compile(r"^(초|중|고)([1-6])$")


def _school_year(today: date | None = None) -> int:
    today = today or date.today()
    return today.year if today.month >= 3 else today.year - 1


def birth_year_to_grade(birth_year: int, today: date | None = None) -> str | None:
    """Recommend 초1~고3, N수, 성인 from birth year."""
    if birth_year < 1900 or birth_year > date.today().year:
        return None
    school_year = _school_year(today)
    # 3월 학년도 기준: 2008년생 → 2026학년도 고3
    years_in_school = school_year - birth_year - 7
    if years_in_school < 0:
        return None
    if years_in_school <= 5:
        return f"초{years_in_school + 1}"
    if years_in_school <= 8:
        return f"중{years_in_school - 5}"
    if years_in_school <= 11:
        return f"고{years_in_school - 8}"
    if years_in_school == 12:
        return "N수"
    return "성인"


def grade_to_birth_year(grade: str, today: date | None = None) -> int | None:
    """Recommend birth year from grade label (초1~고3)."""
    grade = (grade or "").strip()
    m = GRADE_PATTERN.match(grade)
    if not m:
        return None
    school_year = _school_year(today)
    kind, num = m.group(1), int(m.group(2))
    if kind == "초" and 1 <= num <= 6:
        years_in_school = num - 1
    elif kind == "중" and 1 <= num <= 3:
        years_in_school = 5 + num
    elif kind == "고" and 1 <= num <= 3:
        years_in_school = 8 + num
    else:
        return None
    return school_year - 7 - years_in_school


def grade_suggestions_for_birth_year(birth_year: int) -> list[str]:
    """Primary + nearby grades for datalist."""
    primary = birth_year_to_grade(birth_year)
    if not primary:
        return []
    order = [f"초{i}" for i in range(1, 7)] + [f"중{i}" for i in range(1, 4)] + [
        f"고{i}" for i in range(1, 4)
    ]
    if primary not in order:
        return [primary]
    idx = order.index(primary)
    out: list[str] = []
    for i in range(max(0, idx - 1), min(len(order), idx + 2)):
        out.append(order[i])
    return out
