# 테스트 (단위 → 통합 → API)

기능을 **단계별로** 검증합니다. `docs/기능요구서.md`의 FR(M/S)와 docstring으로 대응합니다.

## 디렉터리

```
tests/
  unit/                         # DB 없음 — 순수 로직
  integration/
    accounts/                   # ACC: 가입·로그인·인증·axes·2FA
    students/                   # STU: ORM·웹·timezone API
    calendar/                   # CAL: 서비스·materialize·duration
    reports/                    # RPT: 주간 서비스·컬럼·웹
    progress/                   # PRG: 진도·수업 메모
    web/                        # 웹 SSR 접근 제어·달력
    api/                        # MOB: JWT·REST HTTP
  factories.py
  conftest.py
```

| 레이어 | 마커 | 포함 내용 |
|--------|------|-----------|
| **단위** | `unit` | ISO 주차, UI 상태, 특이사항 포맷, 요일, 마스킹, TZ 제안 |
| **통합** | `integration` | Django DB + 서비스·웹 `client` |
| **API** | `api` + `integration` | DRF HTTP (`/api/v1/...`) |

## 환경 (uv)

```bash
uv sync --all-groups
```

## 실행 순서 (권장)

```bash
uv run pytest tests/unit -m unit -q
uv run pytest tests/integration -m "integration and not api" -q
uv run pytest tests/integration/api -m api -q
uv run pytest -q
```

## FR 커버리지 요약

| 영역 | 주요 테스트 파일 |
|------|------------------|
| ACC | `integration/accounts/` |
| STU | `integration/students/`, `api/test_students_api.py`, `test_subjects_api.py` |
| CAL | `integration/calendar/`, `api/test_calendar_api.py`, `test_lesson_api.py`, `web/test_calendar_web.py` |
| PRG | `integration/progress/` |
| RPT | `integration/reports/`, `api/test_weekly_api.py` |
| MOB | `integration/api/` |

**1차 제외**: 엑셀보내기(FR-PRG-04, FR-RPT-09), Android UI, OPS/Docker smoke, 소셜 OAuth E2E.

## TDD 흐름

1. **단위** 녹색 — `core/`, 포맷터
2. **통합** 녹색 — 서비스·웹
3. **API** 녹색 — View·URL
4. 기능요구서 `FR-*` ↔ 테스트 파일 docstring

## 커버리지 (선택)

```bash
uv run pytest --cov=accounts --cov=students --cov=calendar_app --cov=reports --cov=api --cov=core -q
```
