#!/bin/sh
# Container start-up: prepare data folders, migrate the database, load demo data
# on the very first start, then hand over to Gunicorn (CMD).
set -e

mkdir -p "${DJANGO_DATA_DIR:-/app/data}/media" "${DJANGO_DATA_DIR:-/app/data}/private_media"

echo "==> Applying database migrations"
python manage.py migrate --noinput

if [ "${SEED_DEMO_ON_START:-true}" = "true" ]; then
  echo "==> Checking demo data"
  python manage.py seed_if_empty
fi

# Optional: set your own admin password on the server instead of admin123
python manage.py set_admin_password

echo "==> Starting: $*"
exec "$@"
