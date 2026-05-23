"""Parse 진도차트.xls (Sheet1) for progress chart import."""

from __future__ import annotations

import re
import struct
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any

import xlrd
from django.utils import timezone as django_tz

WEEKDAYS = set("월화수목금토일")
TIME_RANGE_RE = re.compile(
    r"^(?P<start>\d{1,2}:\d{2})\s*~\s*(?P<end>\d{1,2}:\d{2})$"
)
HEADER_ROW = 3  # 0-based row 4 in Excel
DATA_START_ROW = 4  # 0-based row 5
COL_LESSON_NUMBER = 1  # B
COL_DATE = 2  # C
COL_WEEKDAY = 3  # D
COL_TIME = 4  # E
COL_CONTENT = 5  # F
COL_NOTES = 6  # G

TEXTBOX_KEYS = ("textbox_1", "textbox_4", "textbox_5", "textbox_6")


@dataclass
class ParsedMeta:
    age: int | None = None
    student_name: str = ""
    teacher_name: str = ""
    subject: str = ""
    valid: dict[str, bool] = field(default_factory=dict)


@dataclass
class ParsedLessonRow:
    row_index: int
    lesson_number: int | None = None
    lesson_date: date | None = None
    weekday: str = ""
    time_range: str = ""
    start_time: time | None = None
    end_time: time | None = None
    lesson_content: str = ""
    lesson_notes: str = ""
    valid: dict[str, bool] = field(default_factory=dict)

    def to_review_dict(self) -> dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "row_index": self.row_index,
            "lesson_number": self.lesson_number,
            "date": self.lesson_date.isoformat() if self.lesson_date else "",
            "weekday": self.weekday,
            "time_range": self.time_range,
            "start_time": self.start_time.strftime("%H:%M") if self.start_time else "",
            "end_time": self.end_time.strftime("%H:%M") if self.end_time else "",
            "lesson_content": self.lesson_content,
            "lesson_notes": self.lesson_notes,
            "valid": dict(self.valid),
        }


def _cell_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value).strip()


def _parse_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, float):
        if value != int(value):
            return None
        return int(value)
    text = str(value).strip()
    if not text or text == "/":
        return None
    if text.isdigit():
        return int(text)
    return None


def _parse_date_cell(sheet: xlrd.sheet.Sheet, rowx: int, colx: int, book: xlrd.book.Book) -> date | None:
    cell_type = sheet.cell_type(rowx, colx)
    value = sheet.cell_value(rowx, colx)
    if cell_type == xlrd.XL_CELL_DATE:
        try:
            dt = xlrd.xldate.xldate_as_datetime(value, book.datemode)
            return dt.date()
        except (xlrd.XLDateError, ValueError):
            return None
    if cell_type == xlrd.XL_CELL_NUMBER:
        try:
            dt = xlrd.xldate.xldate_as_datetime(value, book.datemode)
            return dt.date()
        except (xlrd.XLDateError, ValueError):
            pass
    text = _cell_str(value)
    if not text or text == "/":
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    # mm/dd without year — cannot infer reliably
    if re.match(r"^\d{1,2}/\d{1,2}$", text):
        return None
    return None


def _parse_weekday(value: Any) -> tuple[str, bool]:
    text = _cell_str(value)
    if not text or text == "/":
        return "", False
    if len(text) == 1 and text in WEEKDAYS:
        return text, True
    return text, False


def _parse_time_range(value: Any) -> tuple[str, time | None, time | None, bool]:
    text = _cell_str(value)
    if not text or text == "/":
        return "", None, None, False
    match = TIME_RANGE_RE.match(text.replace(" ", ""))
    if not match:
        return text, None, None, False
    try:
        start = datetime.strptime(match.group("start"), "%H:%M").time()
        end = datetime.strptime(match.group("end"), "%H:%M").time()
    except ValueError:
        return text, None, None, False
    if end <= start:
        return text, None, None, False
    return f"{start.strftime('%H:%M')}~{end.strftime('%H:%M')}", start, end, True


def _parse_content(value: Any, *, required: bool) -> tuple[str, bool]:
    text = _cell_str(value)
    if text == "/":
        text = ""
    if required:
        return text, bool(text)
    return text, True


def _extract_unicode_strings(blob: bytes, min_len: int = 1) -> list[str]:
    found: list[str] = []
    i = 0
    while i < len(blob) - 2:
        if blob[i + 1] == 0 and blob[i] != 0:
            j = i
            chars = bytearray()
            while j < len(blob) - 1 and blob[j + 1] == 0:
                c = blob[j]
                if c == 0 and chars:
                    break
                if (0x20 <= c < 0x7F) or c >= 0x80:
                    chars.append(c)
                    j += 2
                else:
                    break
            if len(chars) >= min_len * 2:
                try:
                    s = chars.decode("utf-16-le").strip()
                    if s and s not in found and not s.startswith("\x08"):
                        found.append(s)
                except UnicodeDecodeError:
                    pass
            i = max(j, i + 2)
        else:
            i += 1
    return found


def _extract_textboxes_from_workbook(book: xlrd.book.Book) -> dict[str, str]:
    """Best-effort TextBox text extraction from legacy .xls."""
    raw = book.filestr or b""
    if not raw:
        return {}
    texts: list[str] = []
    idx = 0
    while idx < len(raw) - 4:
        if raw[idx : idx + 2] == b"\xb6\x01":
            rec_len = struct.unpack_from("<H", raw, idx + 2)[0]
            chunk = raw[idx : idx + 4 + rec_len + 120]
            for s in _extract_unicode_strings(chunk):
                if len(s) <= 64 and s not in texts:
                    texts.append(s)
            idx += 4 + rec_len
        else:
            idx += 1
    # Filter placeholder / label noise
    cleaned = [
        t
        for t in texts
        if t not in {"Check Cell", "Currency", "Currency [0]", "Explanatory Text", "Good", "Normal", "Note", "Output", "Warning Text"}
        and not t.startswith("Table Style")
        and "돋움" not in t
        and t != "자동길이"
    ]
    result: dict[str, str] = {}
    if cleaned:
        mapping = list(TEXTBOX_KEYS)
        for i, key in enumerate(mapping):
            if i < len(cleaned):
                result[key] = cleaned[i]
    return result


def _parse_meta(book: xlrd.book.Book) -> ParsedMeta:
    boxes = _extract_textboxes_from_workbook(book)
    age = _parse_int(boxes.get("textbox_1", ""))
    student_name = boxes.get("textbox_4", "").strip()
    teacher_name = boxes.get("textbox_5", "").strip()
    subject = boxes.get("textbox_6", "").strip()
    meta = ParsedMeta(
        age=age,
        student_name=student_name,
        teacher_name=teacher_name,
        subject=subject,
    )
    meta.valid = {
        "age": age is not None and age > 0,
        "student_name": bool(student_name),
        "teacher_name": bool(teacher_name),
        "subject": bool(subject),
    }
    return meta


def _cell_is_blank(val: Any) -> bool:
    if val in (None, "", "/"):
        return True
    if isinstance(val, float) and val == 0:
        return True
    return False


def _row_is_empty(sheet: xlrd.sheet.Sheet, rowx: int) -> bool:
    for colx in range(COL_LESSON_NUMBER, COL_NOTES + 1):
        if not _cell_is_blank(sheet.cell_value(rowx, colx)):
            return False
    return True


def _row_only_lesson_number(sheet: xlrd.sheet.Sheet, rowx: int) -> bool:
    """B열만 값이 있고 C~G가 모두 비어 있으면 데이터 없음으로 처리."""
    if _cell_is_blank(sheet.cell_value(rowx, COL_LESSON_NUMBER)):
        return False
    for colx in range(COL_DATE, COL_NOTES + 1):
        if not _cell_is_blank(sheet.cell_value(rowx, colx)):
            return False
    return True


def parse_progress_xls(file_bytes: bytes) -> tuple[ParsedMeta, list[ParsedLessonRow]]:
    book = xlrd.open_workbook(file_contents=file_bytes, formatting_info=False)
    sheet = book.sheet_by_index(0)
    meta = _parse_meta(book)
    lessons: list[ParsedLessonRow] = []
    for rowx in range(DATA_START_ROW, sheet.nrows):
        if _row_is_empty(sheet, rowx):
            continue
        if _row_only_lesson_number(sheet, rowx):
            continue
        lesson_number = _parse_int(sheet.cell_value(rowx, COL_LESSON_NUMBER))
        lesson_date = _parse_date_cell(sheet, rowx, COL_DATE, book)
        weekday, weekday_ok = _parse_weekday(sheet.cell_value(rowx, COL_WEEKDAY))
        time_range, start_time, end_time, time_ok = _parse_time_range(sheet.cell_value(rowx, COL_TIME))
        content, content_ok = _parse_content(sheet.cell_value(rowx, COL_CONTENT), required=True)
        notes, notes_ok = _parse_content(sheet.cell_value(rowx, COL_NOTES), required=False)
        if lesson_number is None and lesson_date is None and not content:
            continue
        row = ParsedLessonRow(
            row_index=rowx + 1,
            lesson_number=lesson_number,
            lesson_date=lesson_date,
            weekday=weekday if weekday_ok else "",
            time_range=time_range if time_ok else (_cell_str(sheet.cell_value(rowx, COL_TIME)) if _cell_str(sheet.cell_value(rowx, COL_TIME)) != "/" else ""),
            start_time=start_time,
            end_time=end_time,
            lesson_content=content if content_ok else "",
            lesson_notes=notes if notes_ok else "",
        )
        row.valid = {
            "lesson_number": lesson_number is not None and lesson_number > 0,
            "date": lesson_date is not None,
            "weekday": weekday_ok,
            "time_range": time_ok,
            "lesson_content": content_ok,
            "lesson_notes": notes_ok,
        }
        lessons.append(row)
    return meta, lessons


def draft_from_parse(meta: ParsedMeta, lessons: list[ParsedLessonRow]) -> dict[str, Any]:
    return {
        "meta": {
            "age": meta.age,
            "student_name": meta.student_name,
            "teacher_name": meta.teacher_name,
            "subject": meta.subject,
            "valid": meta.valid,
        },
        "lessons": [lesson.to_review_dict() for lesson in lessons],
        "imported_at": django_tz.now().isoformat(),
    }
