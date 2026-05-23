"""FR-STU-02~07, STU-09~10, STU-11, STU-12: student web CRUD."""

import pytest

from students.models import GoalHistoryEntry, Student, StudentDetail, Subject


@pytest.mark.integration
def test_student_create_form_korean_labels(logged_in_client):
    res = logged_in_client.get("/students/new/")
    assert res.status_code == 200
    html = res.content.decode()
    assert "<label" in html
    for label in ("이름", "출생 연도", "학년", "시간대", "학부모 성함", "메모", "정규 수업", "1회 수업"):
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
    assert Student.objects.filter(owner=user, name="신규학생").exists()


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
    res = logged_in_client.get(f"/students/progress/{student.pk}/")
    assert res.status_code == 200
    html = res.content.decode()
    assert "진도차트" not in html or student.name in html
    assert 'class="tabs"' not in html
    assert "다른 학생" in html


def test_student_detail_no_tabs(logged_in_client, student):
    res = logged_in_client.get(f"/students/{student.pk}/")
    assert res.status_code == 200
    html = res.content.decode()
    assert 'class="tabs"' not in html
    assert "student-detail-card" in html


def test_lesson_detail_page(logged_in_client, student):
    from tests.factories import LessonFactory

    lesson = LessonFactory(student=student, status="scheduled")
    res = logged_in_client.get(f"/students/{student.pk}/?lesson={lesson.pk}")
    assert res.status_code == 200
    html = res.content.decode()
    assert "lesson-action-lesson" in html
    assert "lesson-action-cancel" in html
    assert "lesson-phase-before" in html
    assert "lesson-phase-complete" in html
    assert 'class="btn btn-secondary">저장</button>' in html
    assert "수업 완료" in html
    assert "취소 처리" in html
    assert "student-detail-card" not in html
    assert f'href="/students/{student.pk}/"' in html.replace(" ", "")
    assert "기본 정보" not in html


@pytest.mark.integration
def test_student_detail_layout_panels(logged_in_client, student):
    Subject.objects.create(owner=student.owner, name="수학")
    student.subjects.add(Subject.objects.get(owner=student.owner, name="수학"))
    res = logged_in_client.get(f"/students/{student.pk}/")
    assert res.status_code == 200
    html = res.content.decode()
    assert "student-detail-card" in html
    assert "기본 정보" in html
    assert "학부모" in html
    assert "수업 설정" in html
    assert "subject-tag" in html


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
