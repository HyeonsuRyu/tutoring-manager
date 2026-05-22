"""Calendar UI state from lesson timing. See docs/calendar.md."""

from datetime import datetime
from typing import Literal

UiState = Literal[
    "upcoming",
    "in_progress",
    "past_incomplete",
    "completed",
    "cancelled",
    "proposed",
]


def compute_ui_state(
    *,
    status: str,
    start: datetime,
    end: datetime,
    now: datetime,
    proposed: bool = False,
) -> UiState:
    if proposed:
        return "proposed"
    if status == "cancelled":
        return "cancelled"
    if status == "completed":
        return "completed"
    if now < start:
        return "upcoming"
    if start <= now < end:
        return "in_progress"
    return "past_incomplete"
