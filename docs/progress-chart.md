# 진도차트·수업 기록 (확정)

**수업별** 수업 내용·비고 작성과, 학생별 **진도차트** 조회·**엑셀 가져오기** 명세입니다.  
**확정일**: 2026-05-22

**관련**: [calendar.md](./calendar.md) (`Lesson`), [students.md](./students.md), [progress-import.md](./progress-import.md)

**범위 외 (추후)**: 엑셀(.xlsx) **보내기**

---

## 요약

| 항목 | 결정 |
|------|------|
| 저장 | `Lesson` 모델에 **수업 내용**·**비고** (회차마다 1건) |
| 편집 | 달력 이벤트 팝오버·(선택) 학생 상세에서 `Lesson` 수정 |
| 진도차트 | 학생별 **테이블 뷰** + **진도 허브** (`/students/progress/`) |
| 표시 컬럼 | 회차, 수업 날짜, 요일, 시간, 수업 내용, 비고 |
| 엑셀 가져오기 | **구현** — 레거시 `진도차트.xls` → 검토 → 카드별 DB 적용 ([progress-import.md](./progress-import.md)) |
| 엑셀보내기 | **미구현** |

---

## `Lesson` 필드

[calendar.md](./calendar.md)의 `Lesson`에 다음을 사용한다.

| 필드 | 타입 | UI 라벨 | 비고 |
|------|------|---------|------|
| `lesson_content` | `TextField` | **수업 내용** | blank=True |
| `lesson_notes` | `TextField` | **비고** | blank=True |

- **제안**(가상 일정)에는 없음 — `Lesson` 생성 후에만 입력·조회
- `GoalHistoryEntry`와 **별개**

### 편집 UI

| 위치 | 동작 |
|------|------|
| 홈 달력 | 이벤트 클릭 → 팝오버: 완료 + 수업 내용·비고 |
| (선택) 학생 상세 | 최근 수업에서 동일 필드 편집 |

---

## 진도차트 페이지

### URL·네비

| 항목 | 값 |
|------|-----|
| 학생별 URL | `/students/<id>/progress/` |
| 허브 | `/students/progress/` — 학생 선택·**데이터 불러오기** |
| 권한 | `student.owner == request.user` |

### 데이터·컬럼

```python
Lesson.objects.filter(student=student).order_by("lesson_number", "start_datetime")
```

| 컬럼 | 출처 |
|------|------|
| 수업 회차 | `lesson_number` |
| 수업 날짜 | `date` / `start_datetime` (학생 TZ) |
| 요일 | `start_datetime` → 학생 `timezone` |
| 시간 | `start_datetime`~`end_datetime` |
| 수업 내용 | `lesson_content` |
| 비고 | `lesson_notes` |

정렬: `lesson_number` 오름차순.

---

## 엑셀 가져오기 (요약)

상세: **[progress-import.md](./progress-import.md)**

1. 허브 또는 `/students/progress/import/`에서 `.xls` 업로드  
2. `/students/progress/import/review/`에서 메타·수업 카드 검토  
3. 학생 선택 후 카드별 **확인 · DB 저장**  
4. 미등록 학생은 **학생 추가** → 엑셀 메타로 `/students/new/` 폼 자동 채움  

템플릿: `resources/excel_templates/진도차트.xls`

---

## API (권장)

| Method | Path | 용도 |
|--------|------|------|
| `GET` | `/students/<id>/progress/` | HTML 테이블 |
| `PATCH` | `/api/v1/lessons/<id>/` | `lesson_content`, `lesson_notes` |

가져오기는 **웹 전용** (1차); REST import API 없음.

---

## 구현 체크리스트

- [x] `Lesson`: `lesson_content`, `lesson_notes`
- [x] 달력 팝오버 편집
- [x] 진도차트 뷰·허브
- [x] 엑셀 가져오기 (`.xls`) — 검토·카드별 적용
- [x] 검토 화면 → 학생 등록 prefill
- [ ] 엑셀보내기

---

## 추후: 엑셀보내기

- `openpyxl` 등
- 컬럼: 회차, 날짜, 요일, 시간, 수업 내용, 비고
- 파일명 예: `{student_name}_진도차트_{YYYYMMDD}.xlsx`

---

## 문서 연동

| 문서 | 반영 |
|------|------|
| [calendar.md](./calendar.md) | `Lesson` 필드·팝오버 |
| [students.md](./students.md) | 상세 링크·등록 prefill |
| [progress-import.md](./progress-import.md) | `.xls` 형식·플로우 전체 |
| [기능요구서.md](./기능요구서.md) | FR-PRG-* |
