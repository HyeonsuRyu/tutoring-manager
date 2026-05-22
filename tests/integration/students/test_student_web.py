"""FR-STU-02~07, STU-09~10, STU-11, STU-12: student web CRUD."""

from datetime import date

import pytest

from students.models import GoalHistoryEntry, Student, StudentDetail, Subject


@pytest.mark.integration
def test_student_create_form_korean_labels(logged_in_client):
    res = logged_in_client.get("/students/new/")
    assert res.status_code == 200
    html = res.content.decode()
    assert "<label" in html
    for label in ("이름", "출생 연도", "학년", "시간대", "학부모 성함", "첫 수업", "메모", "정규 수업", "1회 수업"):
        assert label in html
    assert "보호자" not in html
    assert "국가" not in html
    assert "도시" not in html
    assert "slot-add" in html
    assert "slot-remove-btn" in html
    assert "10,000" in html
    assert "hourly-rate-suffix" in html
    assert "대한민국" in html


@pytest.mark.integration
def test_student_create_without_subjects_shows_settings_button(logged_in_client, user):
    Subject.objects.filter(owner=user).delete()
    res = logged_in_client.get("/students/new/")
    html = res.content.decode()
    assert "과목 설정에서" in html
    assert 'target="_blank"' in html


@pytest.mark.integration
def test_student_list_and_create(logged_in_client, user):
    res = logged_in_client.get("/students/")
    assert res.status_code == 200
    res = logged_in_client.get("/students/?sort=grade")
    assert res.status_code == 200

    subject = Subject.objects.create(owner=user, name="영어")
    res = logged_in_client.post(
        "/students/new/",
        {
            "name": "신규학생",
            "birth_year": 2011,
            "grade": "중1",
            "timezone": "Asia/Seoul",
            "student_contact": "01011112222",
            "parent_name": "",
            "parent_contact": "",
            "first_lesson_date": "2026-04-01",
            "hourly_rate": "50000",
            "lesson_duration_minutes": 60,
            "lessons_completed": 0,
            "subjects": [str(subject.pk)],
            "schedule_slots-TOTAL_FORMS": "1",
            "schedule_slots-INITIAL_FORMS": "0",
            "schedule_slots-MIN_NUM_FORMS": "0",
            "schedule_slots-MAX_NUM_FORMS": "1000",
            "schedule_slots-0-day_of_week": "1",
            "schedule_slots-0-start_time": "19:00",
            "schedule_slots-0-end_time": "20:00",
            "schedule_slots-0-note": "",
            "schedule_slots-0-id": "",
        },
    )
    assert res.status_code == 302
    s = Student.objects.get(owner=user, name="신규학생")
    assert s.first_lesson_date == date(2026, 4, 1)


@pytest.mark.integration
def test_student_detail_memo_and_history(logged_in_client, student):
    StudentDetail.objects.get_or_create(student=student)
    res = logged_in_client.post(
        f"/students/{student.pk}/",
        {"action": "memo", "long_memo": "상담 메모"},
    )
    assert res.status_code == 302
    student.detail.refresh_from_db()
    assert student.detail.long_memo == "상담 메모"

    res = logged_in_client.post(
        f"/students/{student.pk}/",
        {
            "action": "history_add",
            "entry_date": "2026-03-01",
            "entry_type": "goal",
            "title": "목표 설정",
            "body": "수학 90점",
        },
    )
    assert res.status_code == 302
    assert GoalHistoryEntry.objects.filter(detail=student.detail, title="목표 설정").exists()


@pytest.mark.integration
def test_student_progress_page(logged_in_client, student):
    res = logged_in_client.get(f"/students/{student.pk}/progress/")
    assert res.status_code == 200
    html = res.content.decode()
    assert "진도차트" in html
    assert 'class="tab is-active"' in html or "tab is-active" in html


def test_student_detail_has_progress_tab(logged_in_client, student):
    res = logged_in_client.get(f"/students/{student.pk}/")
    assert res.status_code == 200
    html = res.content.decode()
    assert "student-progress" in html or f"/students/{student.pk}/progress/" in html
    assert "진도차트" in html


@pytest.mark.integration
def test_subject_master_web(logged_in_client, user):
    res = logged_in_client.get("/students/settings/subjects/")
    assert res.status_code == 200
    res = logged_in_client.post(
        "/students/settings/subjects/",
        {"name": "과학"},
    )
    assert res.status_code == 200
    assert Subject.objects.filter(owner=user, name="과학").exists()
    subject = Subject.objects.get(owner=user, name="과학")
    res = logged_in_client.post(
        "/students/settings/subjects/",
        {"action": "update", "subject_id": subject.pk, "name": "과학심화"},
    )
    assert res.status_code == 200
    subject.refresh_from_db()
    assert subject.name == "과학심화"


@pytest.mark.integration
def test_student_detail_shows_next_lesson_number(logged_in_client, student):
    student.lessons_completed = 5
    student.save()
    res = logged_in_client.get(f"/students/{student.pk}/")
    assert res.status_code == 200
    assert "6" in res.content.decode()  # next = completed + 1
