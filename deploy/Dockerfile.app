FROM python:3.12-slim
WORKDIR /app
RUN pip install uv && apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
RUN chmod +x deploy/entrypoint.sh
ENV DJANGO_SETTINGS_MODULE=config.settings.base
EXPOSE 8000
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
