"""Mask contact numbers for list display. See docs/students.md."""


def mask_contact(value: str) -> str:
    raw = (value or "").strip()
    if len(raw) <= 4:
        return raw or "—"
    visible = raw[-4:]
    return "*" * max(0, len(raw) - 4) + visible
