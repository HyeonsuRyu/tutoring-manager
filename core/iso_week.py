"""ISO 8601 week (Monday start, week/year by Thursday). See docs/weekly-lesson-status.md."""

from datetime import date, timedelta


def iso_week_range(iso_year: int, iso_week: int) -> tuple[date, date]:
    """Return (Monday, Sunday) for the given ISO year and week number."""
    jan4 = date(iso_year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.isocalendar().weekday - 1)
    week_start = week1_monday + timedelta(weeks=iso_week - 1)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def week_label(iso_week: int, week_start: date, week_end: date) -> str:
    return f"{iso_week}주차 ({week_start:%m.%d}~{week_end:%m.%d})"
