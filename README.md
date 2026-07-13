# Tutoring Manager

Academy tutoring platform (teacher-focused SPA + FastAPI). See `.cursor/rules/` for product and stack conventions.

## Layout

| Path | Role |
|------|------|
| `frontend/` | React + Vite SPA (pnpm, Tailwind, shadcn-ready) |
| `backend/` | FastAPI API (uv, SQLAlchemy 2, Alembic) |
| `deploy/` | Compose (`app`, `web`), dev Mailpit override, host Nginx sample |

Postgres is **external** (not in Compose). Nginx is **not** a Compose service — use `deploy/nginx/*.sample` on the host.

## Prerequisites

- Node 24 + pnpm
- Python 3.13 via [uv](https://docs.astral.sh/uv/)
- Docker (optional)
- PostgreSQL reachable via `DATABASE_URL`

## Backend

```bash
cd backend
cp .env.example .env
uv sync
uv run uvicorn tutoring_manager_api.main:app --reload --port 8000
```

- API prefix: `/api/v1` (e.g. `GET /api/v1/health`)
- Alembic auto-upgrade runs only when `APP_ENV=development`
- Production: run `uv run alembic upgrade head` yourself — never rely on auto-migrate

```bash
uv run pytest
uv run alembic revision --autogenerate -m "msg"
uv run alembic upgrade head
```

## Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Dev server proxies `/api` → `http://localhost:8000`.

```bash
pnpm test
pnpm test:e2e
pnpm build
```

Add shadcn components with:

```bash
pnpm dlx shadcn@latest add button
```

## Docker

```bash
# Requires DATABASE_URL and JWT_SECRET in the environment or a .env next to compose
docker compose -f deploy/docker-compose.yml up --build

# Dev mail catcher (Mailpit UI :8025, SMTP :1025)
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml up --build
```

## Display name

Default app title is **Tutoring Manager**, overridable with `APP_NAME` / `VITE_APP_NAME` (frontend wiring can follow later).
