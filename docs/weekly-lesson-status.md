# 주간 수업 현황 (확정)

**연도·주차**를 선택해 해당 주의 **완료·취소** 수업을 시간순으로 조회하는 페이지 명세입니다.  
**확정일**: 2026-05-22

**관련**: [calendar.md](./calendar.md) (`Lesson`), [students.md](./students.md), [progress-chart.md](./progress-chart.md), [api.md](./api.md), [mobile-android.md](./mobile-android.md)

**범위 외 (추후)**: 엑셀 **보내기**

---

## 요약

| 항목 | 결정 |
|------|------|
| 페이지명 | **주간 수업 현황** |
| URL (예) | `/reports/weekly/` |
| 필터 | **연도** + **n주차 (mm.dd~mm.dd)** |
| 대상 수업 | `status` ∈ **`completed`**, **`cancelled`** |
| 정렬 | **시간순** (`start_datetime` 기준; 화면 일부 컬럼은 취소 시 공란) |
| 범위 | 로그인 사용자(`owner`)의 **전체 학생** 수업 |

---

## `Lesson` 모델 확장

[calendar.md](./calendar.md) `Lesson`에 아래 필드를 **추가**한다.

### 공통·수업 분류

| 필드 | 타입 | UI 라벨 | 비고 |
|------|------|---------|------|
| `lesson_kind` | `TextChoices` | 테스트/정규 | `regular`(정규), `test`(테스트); 기본 `regular` |
| `course_name` | `CharField` | **과정명** | blank=True; 예: 「고1 통합과학」 — Subject와 별도 스냅샷 가능 |

- `subject` FK → `Subject` (선택): 있으면 `course_name` 기본값으로 `subject.name` 제안

### 상태 확장

| `status` 값 | 의미 |
|-------------|------|
| `scheduled` | 예정 (주간 현황 **미포함**) |
| `completed` | 완료 |
| `cancelled` | **취소** (주간 현황 **포함**) |

- 취소 시에도 `start_datetime` 등은 **DB에 유지** (주차 필터·정렬용). **표에는 날짜·요일·시간 공란**.

### 취소 전용 (`status == cancelled`일 때 사용)

| 필드 | 타입 | UI 라벨 | 비고 |
|------|------|---------|------|
| `cancelled_by` | `TextChoices` | 취소 주체 | `student`, `teacher` |
| `cancel_reason` | `CharField`(짧게) | 취소 사유 | blank 허용 — 빈 값이면 특이사항 **고정 문구** (아래) |
| `makeup_status` | `TextChoices` | 보강 여부 | `undecided`, `no_makeup`, `scheduled` |
| `makeup_date` | `DateField`, null | 보강 예정일 | `makeup_status == scheduled` 일 때 필수 |

**`makeup_status` 표시 (특이사항 후반)**

| 값 | 특이사항 문구 |
|----|----------------|
| `undecided` | `보강 일자 미정` |
| `no_makeup` | `보강 예정 없음` |
| `scheduled` | `{makeup_date:%m월 %d일} 보강 예정` (예: `05월 22일 보강 예정`) |

### 취소 편집 UI (1차)

- 달력·수업 상세에서 「취소」 액션 → 모달: 주체·사유·보강 여부·보강일
- 취소 처리 시 `status=cancelled` (레코드 삭제 안 함)

---

## 주차 선택 — **ISO 8601** (확정)

말씀하신 **「월요일 시작 + 목요일 기준」** 은 **ISO 8601 주차**와 같습니다.

| 규칙 | ISO 8601 |
|------|----------|
| 한 주의 시작 | **월요일** |
| 한 주의 끝 | **일요일** |
| **몇 주차·어느 연도** 소속 | 그 주의 **목요일**이 속한 연도·주차로 결정 (1월 4일이 항상 1주차에 포함되는 규칙과 동일) |

표시 예: `12주차 (03.17~03.23)` → 2026년 **ISO 제12주**, 구간은 해당 주 **월~일** (`03.17` 월 … `03.23` 일).

### 구현

- Python: `datetime.date.isocalendar()` → `(iso_year, iso_week, weekday)`  
  - `weekday` 1=월 … 7=일
- 주차 범위 계산:

```python
# iso_year, iso_week → week_start(월), week_end(일)
from datetime import date, timedelta

def iso_week_range(iso_year: int, iso_week: int) -> tuple[date, date]:
    # Jan 4 is always in ISO week 1
    jan4 = date(iso_year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.isocalendar().weekday - 1)
    week_start = week1_monday + timedelta(weeks=iso_week - 1)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end
```

| UI | 동작 |
|----|------|
| 연도 | **ISO 연도** (`iso_year`) — 연말·연초 주의 목요일 규칙 반영 |
| 주차 | `12주차 (03.17~03.23)` — `iso_week` + `week_start~week_end` 라벨 |

- 서버: `year`(=iso_year), `week`(=iso_week) → `[week_start, week_end]` (월~일)
- Queryset:

```python
Lesson.objects.filter(
    student__owner=request.user,
    status__in=["completed", "cancelled"],
    start_datetime__date__gte=week_start,
    start_datetime__date__lte=week_end,
).select_related("student").order_by("start_datetime")
```

- 라벨: `f"{iso_week}주차 ({week_start:%m.%d}~{week_end:%m.%d})"` — **시작=월, 끝=일**
- 연도 경계: 2025-12-29~2026-01-04 같은 주는 **목요일(1/1)이 2026**이면 **2026년 1주차**로 취급 (ISO)

---

## 테이블 뷰 (컬럼)

| # | 컬럼 | 출처·규칙 |
|---|------|-----------|
| 1 | **순번** | 목록 순서 1, 2, 3… (시간순 정렬 후) |
| 2 | **날짜** | `completed`: 학생 TZ `date` / `cancelled`: **공란** |
| 3 | **요일** | `completed`: 월~일 / `cancelled`: **공란** |
| 4 | **시간** | `completed`: `HH:MM~HH:MM` (학생 TZ) / `cancelled`: **공란** |
| 5 | **과정명** | `course_name` (없으면 `—` 또는 Subject) |
| 6 | **테스트/정규** | `lesson_kind` → 「정규」「테스트」 |
| 7 | **이름** | `student.name` |
| 8 | **학년** | `student.grade` |
| 9 | **특이사항** | 아래 규칙 |

### 시간 컬럼 — 60분이 아닐 때

- 수업 길이(분) = `(end_datetime - start_datetime)` 또는 `student.lesson_duration_minutes`
- **60분이 아니면** 시간 문자열에 **빨간색** CSS (`text-danger` 등)
- `cancelled`는 시간 칸 공란이므로 색 규칙 **해당 없음**

### 특이사항 컬럼

#### 완료 수업 (`completed`)

- 기본: `lesson_notes` (비고) 있으면 표시
- 없으면 `—` 또는 `lesson_content` 요약(선택)

#### 취소 수업 (`cancelled`)

**앞부분 (취소 사유)**

| 조건 | 문구 |
|------|------|
| `cancelled_by=teacher`, `cancel_reason` 있음 | `{cancel_reason}로 인한 휴강` → 템플릿: **`{주체표시} {cancel_reason}로 인한 휴강`** |
| `cancelled_by=student`, `cancel_reason` 있음 | **`{주체표시} {cancel_reason}로 인한 결석`** |
| `cancelled_by=student`, `cancel_reason` **없음** | **`학생 휴강 요청, 사유 전달 받지 못함`** (고정) |

- `{주체표시}`: 「학생」「교사」 또는 생략 후 사유만 — 구현 시 **`{cancelled_by_label} {cancel_reason}로 인한 {absence_label}`**  
  - `teacher` → absence **휴강**  
  - `student` → absence **결석**

**구분자**: ` / ` (슬래시 양쪽 공백)

**뒷부분 (보강)**

| `makeup_status` | 문구 |
|-----------------|------|
| `undecided` | `보강 일자 미정` |
| `no_makeup` | `보강 예정 없음` |
| `scheduled` | `{makeup_date:%m월 %d일} 보강 예정` |

**예시**

```
교사 개인 사정으로 인한 휴강 / 보강 일자 미정
학생 휴강 요청, 사유 전달 받지 못함 / 보강 예정 없음
학생 가족 행사로 인한 결석 / 05월 28일 보강 예정
```

---

## 화면 구성 (1차)

```
주간 수업 현황
[2026 ▼]  [12주차 (03.17~03.23) ▼]  [조회]

순번 | 날짜 | 요일 | 시간 | 과정명 | 테스트/정규 | 이름 | 학년 | 특이사항
-----|------|------|------|--------|-------------|------|------|--------
  1  | 03.18| 화   | 19:00~20:00 (빨강) | ... | 정규 | 김○ | 중2 | ...
  2  |      |      |      | ... | 정규 | 이○ | 고1 | 교사 ... 휴강 / 보강 일자 미정
```

- 네비: 전역 메뉴 「주간 수업 현황」
- 엑셀 버튼: **미표시** (추후)

---

## API (권장)

| Method | Path | 용도 |
|--------|------|------|
| `GET` | `/reports/weekly/` | HTML (query: `year`, `week`) |
| `GET` | `/api/v1/reports/weekly/` | JSON — [api.md](./api.md) |
| `POST` | `/api/v1/lessons/<id>/cancel/` | 취소 처리 |
| `PATCH` | `/api/v1/lessons/<id>/` | 취소 필드·과정명·kind 수정 |

---

## 홈 달력과의 관계

| 항목 | 동작 |
|------|------|
| `cancelled` | 달력에 **취소 스타일**(회색·취소선 등) 표시 — 구현 세부는 UI |
| 완료 | 기존 완료 버튼 유지 |
| 주간 현황 | **리포트 전용** 집계 뷰 |

---

## 구현 체크리스트

- [ ] `Lesson` 필드·`status=cancelled` 마이그레이션
- [ ] 주차 계산 유틸 + 연도/주차 셀렉트
- [ ] 주간 테이블 뷰·특이사항 포맷터
- [ ] 60분 ≠ 빨간 시간
- [ ] 취소 모달·API
- [ ] (추후) 엑셀보내기

---

## 추후 (범위 외)

- 엑셀보내기 (동일 컬럼)
- 주차별 PDF
