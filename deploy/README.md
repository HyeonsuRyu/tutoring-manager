# Docker 배포 가이드

과외 관리 앱을 Docker Compose로 실행하는 방법입니다.  
상세 명세: [docs/infrastructure.md](../docs/infrastructure.md)

**Windows**, macOS, Linux 모두 **Docker Desktop**(또는 Linux의 Docker Engine)만 있으면 동일하게 올릴 수 있습니다. 컨테이너는 Linux 기반이라 Windows에 Ubuntu를 따로 설치할 필요는 없습니다.

---

## 구성

| 서비스 | 역할 | 포트(기본) |
|--------|------|------------|
| **nginx** | 정적 파일·리버스 프록시 | `127.0.0.1:8080` → 80 |
| **web** | Django + Gunicorn | 내부 8000 |
| **postgres** | PostgreSQL 16 (`embedded` 프로필만) | 내부만 (5432 미공개) |

데이터는 프로젝트 루트 `data/`에 bind mount 됩니다.

| 경로 | 내용 |
|------|------|
| `data/postgres/` | DB 데이터 (embedded) |
| `data/media/` | 업로드 미디어 |
| `data/static/` | `collectstatic` 결과 |

---

## 사전 준비

1. [Docker Desktop](https://docs.docker.com/desktop/) 설치  
   - **Windows**: WSL2 백엔드 권장. 프로젝트는 WSL 디스크에 두면 빌드·DB가 더 빠른 경우가 많습니다.
2. `deploy/.env` 파일 생성 (아래 참고)

---

## 1. 환경 변수 (`.env`)

`deploy` 폴더에서 예시를 복사합니다.

**PowerShell (Windows)**

```powershell
cd d:\workspace\tutoring-manager\deploy
Copy-Item .env.example .env
notepad .env
```

**bash**

```bash
cd deploy
cp .env.example .env
```

### 로컬(Windows·Mac) 최소 설정

| 변수 | 권장 값 | 설명 |
|------|---------|------|
| `DB_BACKEND` | `embedded` | Compose 안에서 Postgres 기동 |
| `DB_HOST` | `postgres` | embedded일 때 서비스 이름 |
| `DB_*` / `POSTGRES_*` | 예시에서 변경 | 비밀번호는 반드시 변경 |
| `SECRET_KEY` | 긴 랜덤 문자열 | Django 시크릿 |
| `DEBUG` | `False` (또는 로컬만 `True`) | |
| `DOMAIN` | `local` | localhost 전용 HTTPS·호스트 |
| `NGINX_BIND` | `127.0.0.1:8080` | 브라우저 접속 주소 |

> `.env`는 **`deploy/.env`** 에 두세요. (`docker-compose.yml`의 `env_file` 기준)

### DB 모드

| `DB_BACKEND` | Postgres 컨테이너 | `DB_HOST` 예 |
|--------------|-------------------|--------------|
| `embedded` | 기동함 (`--profile embedded`) | `postgres` |
| `external` | 없음 | Windows 호스트 DB: `host.docker.internal` |

---

## 2. 기동

### 내장 Postgres (로컬·Windows 개발에 권장)

**PowerShell**

```powershell
cd d:\workspace\tutoring-manager\deploy
docker compose -f docker-compose.yml -f docker-compose.embedded.yml --profile embedded up -d --build
```

**bash**

```bash
cd deploy
docker compose -f docker-compose.yml -f docker-compose.embedded.yml --profile embedded up -d --build
```

접속: **http://127.0.0.1:8080**

첫 기동 시 `entrypoint.sh`가 `migrate`·`collectstatic`을 실행합니다.

### 외부 Postgres만 사용

```bash
cd deploy
# .env: DB_BACKEND=external, DB_HOST=host.docker.internal (Windows) 등
docker compose up -d --build
```

---

## 3. 자주 쓰는 명령

```bash
cd deploy

# 로그
docker compose logs -f web
docker compose logs -f nginx

# 중지
docker compose --profile embedded down

# 이미지 재빌드 후 기동
docker compose -f docker-compose.yml -f docker-compose.embedded.yml --profile embedded up -d --build

# 슈퍼유저 (web 컨테이너 안)
docker compose exec web uv run python manage.py createsuperuser
```

---

## 4. Windows 참고

| 항목 | 설명 |
|------|------|
| **호스트 OS** | 명세의 “Ubuntu 게인 서버”는 **운영 서버** 기준. 개발 PC는 Windows여도 됩니다. |
| **스크립트** | `entrypoint.sh`는 **컨테이너 내부**에서 실행됩니다. |
| **CRLF** | `bad interpreter` 오류 시 `entrypoint.sh`를 LF 줄바꿈으로 저장하세요. |
| **방화벽** | `8080` 로컬 접근 허용. |
| **호스트 Postgres** | `DB_HOST=host.docker.internal` (Docker Desktop) |

프로덕션 메일(Resend) 배포 시 SPF/DKIM 안내:

```bash
sh deploy/check_email_dns.sh your-domain.com
```

---

## 5. 개발 vs Docker

| 방식 | 용도 |
|------|------|
| `uv run python manage.py runserver` | 일상 개발·테스트 (가장 가벼움) |
| Docker Compose | 배포와 동일한 스택 확인, 팀·CI, Postgres 필수 검증 |

로컬 개발은 [프로젝트 README](../README.md)의 **uv** 절을, 배포·인프라는 [infrastructure.md](../docs/infrastructure.md)를 참고하세요.

---

## 6. 문제 해결

| 증상 | 확인 |
|------|------|
| `SECRET_KEY required` 등 기동 실패 | `deploy/.env` 존재·필수 변수 누락 여부 |
| 8080 연결 안 됨 | `docker compose ps`, `NGINX_BIND`, 방화벽 |
| DB 연결 실패 (embedded) | `--profile embedded`와 두 compose 파일 모두 지정했는지 |
| web만 재시작 반복 | `docker compose logs web` — 마이그레이션·env 오류 |
| static 404 | `collectstatic` — entrypoint 또는 `docker compose exec web uv run python manage.py collectstatic` |

---

## 파일 목록

| 파일 | 설명 |
|------|------|
| `docker-compose.yml` | web, nginx, postgres(프로필) |
| `docker-compose.embedded.yml` | web → postgres `depends_on` |
| `Dockerfile.app` | Python 3.12 + uv + Gunicorn |
| `entrypoint.sh` | migrate, collectstatic, gunicorn |
| `.env.example` | 환경 변수 템플릿 |
| `nginx/default.conf.template` | Nginx 설정 |
