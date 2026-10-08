# BhoomiDirect Agra - production image
# Builds CSS/JS (minified + collected) into the image, so static files always load.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_DATA_DIR=/app/data \
    DJANGO_STATIC_ROOT=/app/staticfiles

WORKDIR /app

# Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Application code, templates, static files and the bundled real photos
COPY . .

# Build minified assets and collect all static files (CSS, JS, images, admin) into the image
RUN DJANGO_DEBUG=false DJANGO_SECRET_KEY=build-only python manage.py minify_assets \
 && DJANGO_DEBUG=false DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput \
 && chmod +x docker/entrypoint.sh \
 && useradd --create-home --uid 1000 app \
 && mkdir -p /app/data \
 && chown -R app:app /app/data

USER app

# Database (SQLite), uploads and private documents live here: mount a volume
VOLUME ["/app/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz/', timeout=4)" || exit 1

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["sh", "-c", "gunicorn agra_realestate.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3} --timeout ${GUNICORN_TIMEOUT:-60} --access-logfile - --error-logfile -"]
