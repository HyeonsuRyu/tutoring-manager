#!/bin/sh
set -eu

: "${SECRET_KEY:?SECRET_KEY required}"
: "${DB_BACKEND:?DB_BACKEND required}"
: "${DB_HOST:?DB_HOST required}"
: "${DB_PORT:?DB_PORT required}"
: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"
: "${DB_PASSWORD:?DB_PASSWORD required}"

echo "DOMAIN=${DOMAIN:-local}"
if [ -n "${RESEND_API_KEY:-}" ] && [ "${DOMAIN:-local}" != "local" ] && [ "${DOMAIN:-local}" != "" ]; then
  echo "NOTE: Verify SPF/DKIM for ${DOMAIN} before production mail — see docs/email-deliverability.md"
fi
uv run python manage.py migrate --noinput
uv run python manage.py collectstatic --noinput

exec uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2
