# Dockerfile для сервиса olenevod-api (один образ для api / bots / worker,
# разница — в команде запуска, см. docker-compose.yml).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Системные зависимости для сборки asyncpg / psycopg (если потребуются).
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY olenevod ./olenevod
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

EXPOSE 8000

CMD ["uvicorn", "olenevod.main:app", "--host", "0.0.0.0", "--port", "8000"]
