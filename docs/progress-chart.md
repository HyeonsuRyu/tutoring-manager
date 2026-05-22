# 진도차트·수업 기록 (확정)

**수업별** 수업 내용·비고 작성과, 학생별 **진도차트** 조회 페이지 명세입니다.  
**확정일**: 2026-05-22

**관련**: [calendar.md](./calendar.md) (`Lesson`), [students.md](./students.md) (`Student`, timezone)

**범위 외 (추후)**: 엑셀(.xlsx) **보내기**

---

## 요약

| 항목 | 결정 |
|------|------|
| 저장 | `Lesson` 모델에 **수업 내용**·**비고** (회차마다 1건) |
| 편집 | 달력 이벤트 팝오버·(선택) 학생 상세에서 `Lesson` 수정 |
| 진도차트 | 별도 페이지 — 학생별 **테이블 뷰** (읽기 전용 UI, 필드 편집은 Lesson 폼) |
| 표시 컬럼 | 회차, 수업 날짜, 요일, 시간, 수업 내용, 비고 |
| 엑셀 | **미구현** — 이후 확장 |

---

## `Lesson` 필드 추가

[calendar.md](./calendar.md)의 `Lesson`에 다음을 추가한다.

| 필드 | 타입 | UI 라벨 | 비고 |
|------|------|---------|------|
| `lesson_content` | `TextField` | **수업 내용** | blank=True; 진도·단원·학습 주제 등 |
| `lesson_notes` | `TextField` | **비고** | blank=True; 숙제·특이사항·부모 전달 등 |

- **제안**(가상 일정)에는 없음 — `Lesson` 생성 후에만 입력·조회
- `GoalHistoryEntry`([students.md](./students.md) 상세 이력)와 **별개**: 이력은 상담·목표 로그, `lesson_*`는 **해당 회차 수업** 기록

### 편집 UI (1차)

| 위치 | 동작 |
|------|------|
| 홈 달력 | 이벤트 클릭 → 팝오버/모달: 완료 버튼 + **수업 내용**·**비고** textarea |
| (선택) 학생 상세 | 최근 수업 목록에서 동일 필드 편집 링크 |

저장: `PATCH /api/lessons/<id>/` 또는 폼 POST.

---

## 진도차트 페이지

### 목적

학생 한 명의 **완료·예정 `Lesson` 전체**를 시간순 표로 한눈에 보기 (진도 관리·상담 자료).

### URL·네비

| 항목 | 예 |
|------|-----|
| URL | `/students/<id>/progress/` |
| 메뉴 | 「진도차트」 — 학생 상세·목록에서 링크 |
| 권한 | `student.owner == request.user` |

### 데이터 소스

```python
Lesson.objects.filter(student=student).order_by("lesson_number", "start_datetime")
```

- **제안**(proposed) 일정은 `Lesson`이 없으므로 **표에 미포함**
- DnD·날짜 변경 후에도 `start_datetime`·`date` 기준으로 요일·시간 재계산

### 테이블 컬럼 (뷰)

| 컬럼 | 출처 | 표시 예 |
|------|------|---------|
| **수업 회차** | `lesson_number` | `3` |
| **수업 날짜** | `date` 또는 `start_datetime` → 학생 TZ 날짜 | `2026-05-22` |
| **요일** | `start_datetime` → 학생 `timezone` | `월` |
| **시간** | `start_datetime`~`end_datetime` → 학생 TZ | `19:00–20:30` |
| **수업 내용** | `lesson_content` | 텍스트 (길면 줄임 + 전체 툴팁) |
| **비고** | `lesson_notes` | 동일 |

정렬 기본: **`lesson_number` 오름차순** (회차 순).

### 화면 구성 (1차)

```
[학생 이름] 진도차트          [← 학생 상세]
┌────┬──────────┬────┬──────────┬────────────┬──────┐
│ 회차│ 날짜     │ 요일│ 시간     │ 수업 내용  │ 비고 │
├────┼──────────┼────┼──────────┼────────────┼──────┤
│ 1  │ 2026-01-05│ 일 │ 14:00-… │ ...        │ ...  │
│ 2  │ ...      │ ...│ ...      │ ...        │ ...  │
└────┴──────────┴────┴──────────┴────────────┴──────┘
(엑셀보내기 버튼 — 추후 비활성 또는 미표시)
```

- 빈 필드: `—` 또는 빈 칸
- 행 클릭(선택): 해당 수업 팝오버 편집 또는 달력 해당 일로 이동

### 구현 방식

| 방식 | 설명 |
|------|------|
| **Django 템플릿** | `Lesson` queryset → `<table>` — 1차 권장 |
| DB **VIEW** | PostgreSQL VIEW는 **선택**; ORM queryset으로 동일 결과 가능 → **1차는 VIEW 없이** 템플릿+queryset |
| API | 추후 SPA 시 `GET /api/students/<id>/lessons/` JSON |

PostgreSQL VIEW 예 (참고용, 필수 아님):

```sql
-- lesson_progress_view (선택적 최적화)
SELECT lesson_number, date, ... 
FROM lessons_lesson WHERE student_id = ?;
```

---

## API (권장)

| Method | Path | 용도 |
|--------|------|------|
| `GET` | `/students/<id>/progress/` | HTML 테이블 |
| `PATCH` | `/api/v1/lessons/<id>/` | `lesson_content`, `lesson_notes` — [api.md](./api.md) |

---

## 구현 체크리스트

- [ ] `Lesson` 마이그레이션: `lesson_content`, `lesson_notes`
- [ ] 달력 팝오버 편집 폼
- [ ] 진도차트 뷰·URL·네비 링크
- [ ] 요일·시간 포맷 헬퍼 (`zoneinfo`, `strftime`)
- [ ] (추후) 엑셀보내기

---

## 추후: 엑셀보내기 (범위 외)

- `openpyxl` 또는 `django-import-export`
- 동일 컬럼: 회차, 날짜, 요일, 시간, 수업 내용, 비고
- 파일명 예: `{student_name}_진도차트_{YYYYMMDD}.xlsx`
- 진도차트 페이지에 「엑셀보내기」버튼 추가

---

## 문서 연동

| 문서 | 반영 |
|------|------|
| [calendar.md](./calendar.md) | `Lesson` 필드·팝오버 편집 |
| [students.md](./students.md) | 상세 → 진도차트 링크 |
