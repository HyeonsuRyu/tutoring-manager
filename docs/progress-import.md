# 진도차트 엑셀 가져오기 (확정)

레거시 **진도차트.xls** 파일을 업로드해 수업 기록을 검토한 뒤, 학생별 **완료 `Lesson`**으로 DB에 반영하는 기능 명세입니다.

**확정일**: 2026-05-22  
**관련**: [progress-chart.md](./progress-chart.md), [students.md](./students.md), [calendar.md](./calendar.md)

---

## 요약

| 항목 | 결정 |
|------|------|
| 파일 형식 | Excel **97–2003** (`.xls`), 시트 `Sheet1` |
| 템플릿 | `resources/excel_templates/진도차트.xls` |
| 파서 | `xlrd` (`students/progress_xls.py`) |
| 플로우 | 업로드 → **검토(카드)** → 학생 선택 → 카드별 **확인 · DB 저장** |
| 메타 → 학생 | 검토 화면 **학생 추가** → 등록 폼 자동 채움 (`?from_progress_import=1`) |
| 세션 | `progress_import_draft` (업로드~적용 완료까지 유지) |
| 엑셀보내기 | **미구현** (추후) |

---

## URL·화면

| Method | Path | 이름 | 설명 |
|--------|------|------|------|
| GET | `/students/progress/` | `progress-hub` | 진도 허브 — 「데이터 불러오기」 |
| GET/POST | `/students/progress/import/` | `progress-import` | 파일 업로드 |
| GET | `/students/progress/import/review/` | `progress-import-review` | 검토·카드별 적용 |
| POST | `/students/progress/import/apply/` | `progress-import-apply` | 단일 카드 DB 저장 (JSON) |
| GET | `/students/progress/import/template/` | `progress-import-template` | 공식 템플릿 다운로드 |

진입: **진도차트** 허브(`/students/progress/`) → 「데이터 불러오기」.

---

## 엑셀 파일 형식 (`Sheet1`)

행·열은 **0이 아닌 Excel 1-based** 기준으로 설명한다.

### 상단 메타 (ActiveX TextBox, B열 기준 추출)

| TextBox | 의미 | 파서 키 | 학생 폼 매핑 |
|---------|------|---------|----------------|
| TextBox1 | **나이** (한국식 세는 나이, 정수) | `meta.age` | `birth_year` = 올해 − 나이 + 1, `grade` = `birth_year_to_grade()` 추천 |
| TextBox4 | **학생 이름** | `meta.student_name` | `name` |
| TextBox5 | **교사 이름** | `meta.teacher_name` | 상세 **긴 메모**에 `담당 교사: …` |
| TextBox6 | **과목** | `meta.subject` | `Subject` get_or_create 후 `subjects` M2M 선택 |

> TextBox 문자열은 `.xls` 바이너리에서 **휴리스틱 추출**한다. 파일·엑셀 버전에 따라 비어 있거나 순서가 어긋날 수 있으며, 검토·등록 화면에서 수동 보정한다.

### 수업 표 (4행 헤더, 5행~ 데이터)

| 열 | 헤더(예) | 필드 | 파싱 규칙 |
|----|----------|------|-----------|
| **B** | NO | 회차 (`lesson_number`) | 정수 |
| **C** | 수업날짜 | 날짜 | `yyyy-mm-dd` 등, xlrd 날짜 셀 |
| **D** | 요일 | 요일 | `월`~`일` 한 글자 |
| **E** | 시간 | 시간대 | `hh:mm~hh:mm` (공백 허용), 종료 > 시작 |
| **F** | 수업내용 | 수업 내용 | 필수(비어 있으면 `/` 제외 시 무효) |
| **G** | 비고 | 비고 | 선택, `/` → 빈 문자열 |

**행 포함 규칙**

- B~G가 모두 비어 있으면 **행 무시**.
- **B열만** 값이 있고 C~G가 비어 있으면 **카드 생성 안 함** (빈 회차 placeholder).
- 그 외 C~G 중 하나라도 값이 있으면 검토 **카드 1건** 생성.

### DB 적용 시 (`apply_progress_import`)

- 대상 학생을 검토 화면에서 선택.
- 카드 1건당 `Lesson` **완료** 상태로 생성·갱신: `lesson_number`, `date`, `start_datetime`/`end_datetime`(학생 `timezone`), `lesson_content`, `lesson_notes`.
- 적용 성공 시 해당 카드는 세션 draft에서 제거.

---

## 검토 UI

| 요소 | 동작 |
|------|------|
| 메타 요약 | 나이·이름·교사·과목 표시 (`meta.valid`로 누락 표시) |
| 학생 선택 | 기존 학생 드롭다운 |
| **학생 추가** | `/students/new/?from_progress_import=1` (새 탭) — 세션 draft의 `meta`로 폼 prefill |
| 수업 카드 | 회차·날짜·요일·시간·내용·비고 편집 가능 |
| 카드 사이 **+** | 빈 카드 삽입 |
| **확인 · DB 저장** | 카드 1건씩 AJAX POST → `progress-import-apply` |
| 일괄 적용 | **없음** (카드별 확인만) |

정적 자산: `static/progress_import.js`, `static/app.css` (import 카드·검토 레이아웃).

---

## 학생 등록 자동 채움

| 조건 | 동작 |
|------|------|
| `GET /students/new/?from_progress_import=1` | 세션에 `progress_import_draft`가 있을 때만 |
| POST 요청 | prefill 미적용 (사용자 입력 우선) |
| draft 없음 / meta 비어 있음 | 일반 빈 등록 폼 |

구현: `students/import_prefill.py`, `StudentCreateView` (`students/views.py`).

화면 상단 안내: 「진도차트 엑셀에서 읽은 정보로 아래 필드를 채웠습니다」.

---

## 구현 파일

| 경로 | 역할 |
|------|------|
| `students/progress_xls.py` | `.xls` 파싱 |
| `students/progress_import_apply.py` | 검증·DB 적용 |
| `students/views_progress_import.py` | 업로드·검토·적용 뷰 |
| `students/import_prefill.py` | 학생 등록 initial |
| `templates/students/progress_hub.html` | 허브 |
| `templates/students/progress_import_upload.html` | 업로드 |
| `templates/students/progress_import_review.html` | 검토 |

---

## 제한·알려진 이슈

| 항목 | 내용 |
|------|------|
| 확장자 | `.xlsx` **미지원** (`.xls`만) |
| 업로드 크기 | 5MB |
| TextBox | 추출 실패 시 메타·prefill 일부 누락 |
| 제안 일정 | import 대상 아님 — `Lesson` row만 |
| 소유권 | 적용·prefill 모두 `request.user` 기준 |

---

## 테스트

- `tests/unit/students/test_progress_xls.py`
- `tests/unit/students/test_import_prefill.py`
- `tests/integration/progress/test_progress_import.py`
