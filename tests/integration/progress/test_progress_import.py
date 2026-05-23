"""Progress chart Excel import flow."""

from datetime import date
from io import BytesIO
from pathlib import Path

import pytest
import xlwt
from django.core.files.uploadedfile import SimpleUploadedFile

TEMPLATE = Path("resources/excel_templates/진도차트.xls")


def _sample_xls_bytes() -> bytes:
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
    sh.write(4, 1, 1)
    sh.write(4, 2, date(2024, 5, 1), date_style)
    sh.write(4, 3, "수")
    sh.write(4, 4, "19:00~20:30")
    sh.write(4, 5, "테스트")
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.integration
def test_progress_hub_has_import_button(logged_in_client):
    res = logged_in_client.get("/students/progress/")
    html = res.content.decode()
    assert res.status_code == 200
    assert "데이터 불러오기" in html


@pytest.mark.integration
def test_upload_sample_redirects_to_review(logged_in_client):
    res = logged_in_client.post(
        "/students/progress/import/",
        {"file": SimpleUploadedFile("sample.xls", _sample_xls_bytes(), "application/vnd.ms-excel")},
    )
    assert res.status_code == 302
    assert res.url == "/students/progress/import/review/"
    review = logged_in_client.get("/students/progress/import/review/")
    html = review.content.decode()
    assert review.status_code == 200
    assert "가져오기 검토" in html
    assert "import-lesson-list" in html
    assert "progress_import.js" in html
    assert "from_progress_import=1" in html


@pytest.mark.integration
def test_upload_template_without_data_rows_warns(logged_in_client):
    if not TEMPLATE.exists():
        pytest.skip("template missing")
    with TEMPLATE.open("rb") as f:
        res = logged_in_client.post(
            "/students/progress/import/",
            {"file": f},
            format="multipart",
        )
    assert res.status_code == 302
    assert res.url == "/students/progress/import/"


@pytest.mark.integration
def test_confirm_single_lesson_applies_and_updates_session(logged_in_client, student):
    import json

    from calendar_app.models import Lesson

    logged_in_client.post(
        "/students/progress/import/",
        {"file": SimpleUploadedFile("sample.xls", _sample_xls_bytes(), "application/vnd.ms-excel")},
    )
    draft = logged_in_client.session["progress_import_draft"]
    lesson_id = draft["lessons"][0]["id"]
    logged_in_client.get("/students/progress/import/review/")
    csrf = logged_in_client._client.cookies["csrftoken"].value
    res = logged_in_client.post(
        "/students/progress/import/apply/",
        data=json.dumps(
            {
                "single": True,
                "student_id": student.pk,
                "draft_lesson_id": lesson_id,
                "lesson": {
                    "date": "2024-05-01",
                    "start_time": "19:00",
                    "end_time": "20:30",
                    "lesson_content": "단원1",
                    "lesson_notes": "",
                },
            }
        ),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["remaining"] == 0
    assert Lesson.objects.filter(student=student, status=Lesson.Status.COMPLETED).count() == 1
    assert logged_in_client.session["progress_import_draft"]["lessons"] == []
