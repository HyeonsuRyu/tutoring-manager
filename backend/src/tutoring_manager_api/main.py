import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tutoring_manager_api.api.v1 import api_router
from tutoring_manager_api.config import get_settings

logger = logging.getLogger(__name__)


def _run_migrations_if_dev() -> None:
    settings = get_settings()
    if not settings.is_development:
        return
    try:
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import create_engine, text

        # Fail fast when Postgres is down so API still boots during local scaffold.
        probe = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3},
        )
        with probe.connect() as conn:
            conn.execute(text("SELECT 1"))

        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")
        logger.info("Applied Alembic migrations (development only)")
    except Exception as exc:
        logger.warning("Skipping auto-migrate (DB unavailable): %s", exc)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _run_migrations_if_dev()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
