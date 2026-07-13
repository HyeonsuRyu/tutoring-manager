# Backend

FastAPI service for Tutoring Manager. Run from this directory so `alembic.ini` resolves correctly.

```bash
uv sync
uv run uvicorn tutoring_manager_api.main:app --reload
uv run pytest
```
