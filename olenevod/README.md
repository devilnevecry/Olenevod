# Olenevod

Olenevod is a commerce platform with a FastAPI core, Next.js storefront, Vite/React admin panel, and Telegram/VK/MAX bot adapters.

## Structure

- `apps/api` - FastAPI application, domain/application/infrastructure layers, Alembic migrations.
- `apps/web` - Next.js 15 storefront.
- `apps/admin` - Vite + React admin panel.
- `apps/bots` - Bot adapters.
- `packages/*` - Shared UI, design tokens, motion.
- `infra` - Docker Compose and infrastructure.

## Requirements

- Python 3.12+
- Node.js 20+
- PostgreSQL 16
- Redis 7
- Docker (optional, recommended)

## Quick start

```bash
cp .env.example .env
make up
```

API health check: http://localhost:8000/healthz

## Quality checks

```bash
make lint
make typecheck
make test
```

## Tests

API tests require PostgreSQL and Redis. The CI workflow starts both services automatically.

```bash
cd olenevod/apps/api
DATABASE_URL=postgresql+psycopg://olenevod:olenevod_dev@localhost:5432/olenevod_test \
REDIS_URL=redis://localhost:6379/0 \
APP_MODE=demo \
pytest -q
```

Web and admin:

```bash
cd olenevod/apps/web && npm ci && npm run lint && npm run typecheck && npm run build
cd olenevod/apps/admin && npm ci && npm run lint && npm run typecheck && npm run build
```

## Notes

- Set `APP_MODE=production` only after replacing placeholder owner credentials.
- Do not commit `.env`, databases, caches, or generated reports.