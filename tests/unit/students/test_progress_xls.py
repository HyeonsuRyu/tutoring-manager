"""Progress chart xls parsing."""

from datetime import date
from io import BytesIO

import pytest
import xlrd
import xlwt

from students.progress_xls import parse_progress_xls


def _build_xls_bytes(rows: list[list]) -> bytes:
    wb = xlwt.Workbook()
    sh = wb.add_sheet("Sheet1")
    sh.write(3, 1, "NO")
    sh.write(3, 2, "수업날짜")
    sh.write(3, 3, "요일")
    sh.write(3, 4, "시간")
    sh.write(3, 5, "수업내용")
    sh.write(3, 6, "비고")
    date_style = xlwt.XFStyle()
    date_style.num_format_str = "YYYY-MM-DD"
    for i, row in enumerate(rows):
        r = 4 + i
        for c, val in enumerate(row):
            col = c + 1
            if isinstance(val, date):
                sh.write(r, col, val, date_style)
            else:
                sh.write(r, col, val)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.unit
def test_parse_valid_lesson_row():
    raw = _build_xls_bytes(
        [
            [1, date(2024, 3, 15), "금", "19:00~20:30", "1단원", "숙제"],
        ]
    )
    meta, lessons = parse_progress_xls(raw)
    assert len(lessons) == 1
    row = lessons[0]
    assert row.lesson_number == 1
    assert row.lesson_date == date(2024, 3, 15)
    assert row.weekday == "금"
    assert row.time_range == "19:00~20:30"
    assert row.lesson_content == "1단원"
    assert row.lesson_notes == "숙제"
    assert row.valid["lesson_content"] is True


@pytest.mark.unit
def test_parse_invalid_date_leaves_blank_valid_false():
    raw = _build_xls_bytes([[2, "/", "월", "19:00~20:30", "내용", ""]])
    _, lessons = parse_progress_xls(raw)
    assert len(lessons) == 1
    assert lessons[0].lesson_date is None
    assert lessons[0].valid["date"] is False


@pytest.mark.unit
def test_parse_skips_row_with_only_lesson_number_column():
    raw = _build_xls_bytes([[5, "", "", "", "", ""]])
    _, lessons = parse_progress_xls(raw)
    assert lessons == []


@pytest.mark.unit
def test_parse_skips_row_with_only_b_and_slash_placeholders():
    raw = _build_xls_bytes([[3, "/", "", "", "", ""]])
    _, lessons = parse_progress_xls(raw)
    assert lessons == []


@pytest.mark.unit
def test_parse_template_file_has_no_cards_for_placeholder_rows():
    from pathlib import Path

    path = Path("resources/excel_templates/진도차트.xls")
    if not path.exists():
        pytest.skip("template missing")
    _, lessons = parse_progress_xls(path.read_bytes())
    assert lessons == []
