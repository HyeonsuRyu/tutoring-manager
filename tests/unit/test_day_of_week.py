"""ScheduleSlot day_of_week mapping (pure, no Django)."""

from datetime import date

from core.day_of_week import MONDAY, date_to_slot_day_of_week


def test_monday_maps_to_model_monday():
    assert date(2026, 3, 16).weekday() == 0
    assert date_to_slot_day_of_week(date(2026, 3, 16)) == MONDAY
