# 인프라 (확정)

과외 관리 웹앱(`tutoring-manager`)의 배포·런타임 인프라 명세입니다.  
**확정일**: 2026-05-22  
**개정**: 2026-05-22 — DB·미디어는 호스트 디렉터리 bind mount로 영속화. 종료 시 `pg_dump` 백업은 **구현하지 않음**.

---

## 요약

| 항목 | 결정 |
|------|------|
| 프레임워크 | Django (서버 렌더링) |
| DB | PostgreSQL |
| 호스트 OS | Ubuntu (게인 서버) |
| 실행 | Docker 컨테이너 |
| 설정 | **컨테이너 내부 환경 변수만** (호스트 `export` 미사용) |
| DB 배치 | `embedded` (내장 Postgres) 또는 `external` (외부·공유 Postgres) |
| 이미지 | `tutoring-app`, `tutoring-postgres` (2종, 역할 분리) |

---

## 아키텍처

### DB 모드 (`DB_BACKEND`)

| `DB_BACKEND` | Postgres 컨테이너 | 배포 |
|--------------|-------------------|------|
| `external` | **기동하지 않음** | 앱 스택만. `DB_HOST`로 외부·공유 Postgres 연결 |
| `embedded` | `tutoring-postgres` 이미지 (`--profile embedded`) | 앱 + Postgres 동일 compose |

```
external:
  [Browser] → [Nginx] → [tutoring-app] → (Docker network / 사설 IP) → [외부 Postgres]

embedded:
  [Browser] → [Nginx] → [tutoring-app] → [tutoring-postgres]
       ↓ media mount              ↓ ./data/postgres → /var/lib/postgresql/data
  ./data/media/
```

### 이미지

| 이미지 | Dockerfile | 포함 | 미포함 |
|--------|------------|------|--------|
| `tutoring-app` | `deploy/Dockerfile.app` | Python, Django, Gunicorn, `entrypoint.sh` | Postgres **서버** |
| `tutoring-postgres` | `deploy/Dockerfile.postgres` (또는 compose에서 `postgres:16` 직접 참조) | Postgres 16 | Django, Nginx, **커스텀 백업 스크립트 없음** |

- **Nginx**: 공식 `nginx:alpine` + `deploy/nginx/default.conf.template` (별도 빌드 없음).
- `DB_BACKEND=external`이면 `tutoring-postgres` 이미지는 **빌드·실행 불필요**.

### 네트워크

- Postgres **5432는 공인 IP에 publish 하지 않음**.
- `external`: Docker external network `infra-db` 또는 VM **사설 IP** + 방화벽(앱 → DB만 허용).
- `embedded`: compose 내부 network만.

---

## 환경 변수

모든 값은 **컨테이너 `environment` / `env_file`** 로만 주입한다.  
Ubuntu 호스트에 `export` 해도 앱·DB 프로세스에는 전달되지 않는다.

운영자는 `deploy/.env`를 compose가 읽어 컨테이너에 넣는다 (git 제외).  
구현 시 `deploy/.env.example` 템플릿을 추가한다.

### `.env` 템플릿 (확정)

```bash
# DB
DB_BACKEND=embedded          # embedded | external
DB_HOST=postgres
DB_PORT=5432
DB_NAME=tutoring
DB_USER=tutoring
DB_PASSWORD=change-me

POSTGRES_USER=tutoring       # embedded 시 postgres 컨테이너
POSTGRES_PASSWORD=change-me
POSTGRES_DB=tutoring

# Django
SECRET_KEY=change-me-long-random-string
DEBUG=False

# 접속 (공란 또는 local → localhost 전용)
DOMAIN=local
# DOMAIN=tutor.example.com   # 프로덕션
```

### 필수 (기동 실패)

| 변수 | 서비스 | 설명 |
|------|--------|------|
| `DB_BACKEND` | web | `embedded` 또는 `external` |
| `DB_HOST` | web | DB 호스트 (`embedded` 시 보통 `postgres`) |
| `DB_PORT` | web | 예: `5432` |
| `DB_NAME` | web | 데이터베이스 이름 |
| `DB_USER` | web | DB 사용자 |
| `DB_PASSWORD` | web | DB 비밀번호 |
| `SECRET_KEY` | web | Django secret |
| `POSTGRES_USER` | postgres | `embedded` 시 필수 |
| `POSTGRES_PASSWORD` | postgres | `embedded` 시 필수 |
| `POSTGRES_DB` | postgres | `embedded` 시 필수 |

검증: Compose `${VAR:?message}`, `web`/`postgres` entrypoint `: "${VAR:?}"`, Django settings required keys.

### 접속 도메인 (`DOMAIN`)

| `DOMAIN` | 동작 |
|----------|------|
| 공란 `""` | **localhost 전용** |
| `local` (대소문자 무시) | 위와 동일 |
| 그 외 (예: `tutor.example.com`) | 해당 도메인으로만 서비스 |

**localhost 전용**

- Django: `ALLOWED_HOSTS = localhost, 127.0.0.1`; HTTPS·secure 쿠키 off.
- Nginx ports: `127.0.0.1:8080:80` (호스트 외부 IP 미노출).

**공개 도메인**

- Django: `ALLOWED_HOSTS = [DOMAIN]`; `CSRF_TRUSTED_ORIGINS = https://{DOMAIN}`; SSL redirect on.
- Nginx: `server_name` = `DOMAIN`; `80:80`, `443:443`; cert volume.

`DOMAIN`은 web·nginx **양쪽 컨테이너**에 동일하게 주입.

### 기타

| 변수 | 설명 |
|------|------|
| `DEBUG` | 프로덕션 `False` 권장 (`DOMAIN=local`과 무관) |

---

## 데이터 영속화 — 호스트 디렉터리 bind mount

Postgres·업로드 파일은 **호스트 경로를 컨테이너에 마운트**하여 컨테이너를 재생성해도 데이터가 호스트에 남도록 한다.

| 용도 | 호스트 경로 | 컨테이너 경로 | 서비스 |
|------|-------------|---------------|--------|
| Postgres 데이터 | `./data/postgres/` | `/var/lib/postgresql/data` | postgres (`embedded`) |
| 업로드·미디어 | `./data/media/` | `/app/media` (또는 `MEDIA_ROOT`) | web (학생 첨부는 [students.md](./students.md) 기준 **미구현**) |
| 수집 정적 파일 (선택) | `./data/static/` | `/app/staticfiles` | web |

- `data/`는 git 제외. 호스트에서 디렉터리·권한(UID/GID)만 맞추면 됨.
- **named volume 대신 bind mount**를 기본으로 한다 (`docker compose down`으로 컨테이너만 제거해도 `./data/postgres` 유지).
- `docker compose down -v`는 named volume 제거용; bind mount 데이터는 호스트에 그대로 남음.
- **주기 `pg_dump`·종료 시 dump**: 인프라 범위 **미구현**. 필요 시 호스트 cron 등으로 **운영자가 별도** 구성.

---

## 디렉터리·Compose

```
deploy/
  Dockerfile.app
  Dockerfile.postgres             # 선택: postgres:16 핀 고정
  docker-compose.yml
  docker-compose.embedded.yml
  nginx/default.conf.template
  .env.example

data/                             # gitignore, 호스트에서 생성
  postgres/                       # embedded DB 데이터
  media/
  static/                         # 선택
```

### 기동

```bash
# 외부 DB
docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d

# 내장 DB
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.embedded.yml \
  --profile embedded --env-file deploy/.env up -d
```

`deploy/.env` 예시는 `DB_BACKEND`, `DOMAIN` 조합별로 `.env.example` 참고.

### external + 공유 DB (VM 분리)

1. `docker network create infra-db`
2. DB VM: Postgres compose → `infra-db` join
3. 앱 VM: `DB_BACKEND=external`, `DB_HOST=postgres`(서비스명) 또는 사설 IP

### embedded (단일 호스트)

- `--profile embedded`로 앱·DB 동시 기동.
- `./data/postgres`, `./data/media` 마운트·디스크 용량 확인.

---

## 운영 체크리스트

- [ ] `DB_BACKEND=external` → `tutoring-postgres` 미배포, `DB_HOST` 정확
- [ ] `DB_BACKEND=embedded` → `./data/postgres` 백업·권한 (호스트 차원, 앱 밖)
- [ ] Postgres 5432 공인 미개방
- [ ] `DEBUG=False` (프로덕션)
- [ ] `DOMAIN` empty/`local` → 127.0.0.1 bind only
- [ ] `./data/media` (및 static) 호스트 백업 정책

---

## 미구현 (애플리케이션)

인프라 명세만 확정됨. 다음은 구현 단계에서 작성한다.

- `Dockerfile.app`, `Dockerfile.postgres`, compose 파일
- `config/settings.py` — `resolve_app_domain()`, DB env
- Django 앱·학생 도메인
