"""ScheduleSlot day_of_week (Sun=0 … Sat=6) vs Python date.weekday() (Mon=0 … Sun=6)."""

from datetime import date

# Align with students.models.ScheduleSlot.DayOfWeek
SUNDAY = 0
MONDAY = 1
TUESDAY = 2
WEDNESDAY = 3
THURSDAY = 4
FRIDAY = 5
SATURDAY = 6


def date_to_slot_day_of_week(d: date) -> int:
    return (d.weekday() + 1) % 7
