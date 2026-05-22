# tutoring-manager

과외 학생·수업 일정·진도·주간 현황 관리. 명세는 [docs/](docs/) 참고.

**범위 외(미구현)**: 엑셀보내기 (진도차트·주간 현황)

## 개발 환경 (uv)

[uv](https://docs.astral.sh/uv/)로 Python·의존성을 격리합니다.

```bash
uv sync --all-groups
uv run python manage.py migrate   # 모델 변경 후 필수 (예: accounts_user.username)
uv run python manage.py createsuperuser   # 선택
uv run python manage.py runserver
# http://127.0.0.1:8000/ — allauth 로그인 후 달력·학생·주간 현황

uv run pytest -q
uv run python manage.py check
```

### 인증·보안 (로컬)

- **allauth**: 이메일 로그인·회원가입·이메일 인증(로컬은 콘솔 메일)
- **소셜**: Google / GitHub / Naver — `GOOGLE_*`, `GITHUB_*`, `NAVER_*` 환경 변수
- **2FA**: `/accounts/2fa/setup/` — TOTP + 백업 코드
- **axes**: 로그인 실패 잠금 (테스트 설정에서는 비활성)
- **비밀번호**: Argon2

테스트·TDD: [tests/README.md](tests/README.md)

## Docker 배포

**Windows / macOS / Linux** 모두 [Docker Desktop](https://docs.docker.com/desktop/)으로 동일하게 실행합니다.

1. `deploy/.env.example` → `deploy/.env` 복사 후 `SECRET_KEY`, DB 비밀번호 등 수정
2. 내장 Postgres로 기동:

```powershell
# Windows PowerShell
cd deploy
docker compose -f docker-compose.yml -f docker-compose.embedded.yml --profile embedded up -d --build
```

→ **http://127.0.0.1:8080**

자세한 절차·문제 해결: **[deploy/README.md](deploy/README.md)** · 명세: [docs/infrastructure.md](docs/infrastructure.md)

## Android (Kotlin + Compose)

MVP 스캐폴딩: [android/README.md](android/README.md) — JWT 로그인·토큰 저장. API 베이스 URL은 빌드 시 설정.

## API

DRF JWT: `/api/v1/` — [docs/api.md](docs/api.md)

## 문서

| 문서 | 설명 |
|------|------|
| [기능요구서](docs/기능요구서.md) | 기능 요구 (FR-*) |
| [시스템 사양서](docs/시스템%20사양서.md) | 기술 사양 |
| [infrastructure.md](docs/infrastructure.md) | Docker·DOMAIN |
| [auth.md](docs/auth.md) | 인증·2FA |
| [students.md](docs/students.md) 등 | 도메인 상세 |
