# socialMS

Social service for PersonalCook.

## Overview
SocialMS handles follows, likes, saved recipes, and comments. It stores social data in PostgreSQL and validates recipe/user existence via upstream services.

## Architecture
- FastAPI service with PostgreSQL persistence.
- Uses JWT auth for user-scoped actions.
- Calls recipe and user services for validation.

## Local dev
1. docker network create personalcook-net
2. copy .env.example .env
3. docker compose up --build

## Configuration
Environment variables (see `.env.example`):
- `DATABASE_URL`: Postgres connection string.
- `JWT_SECRET`, `JWT_ALGORITHM`: JWT validation for protected endpoints.
- `RECIPE_SERVICE_URL`: recipe service base URL.
- `USER_SERVICE_URL`: user service base URL.

## Dependencies
- recipe service at RECIPE_SERVICE_URL (default http://recipe_service:8000/recipes)
- user service at USER_SERVICE_URL (default http://user_service:8000/users)

## Ports
- API: 8003
- Postgres: 5434

## API Docs
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc
- OpenAPI JSON: http://localhost:8003/openapi.json

## Testing
Run tests locally:
```
pytest
```

## CI
This repo runs two GitHub Actions jobs:
- `test`: installs requirements and runs `pytest`
- `container`: builds the Docker image, starts Postgres, runs the container, and hits `/` for a smoke test

Tests (files and intent):
- `tests/test_social_routes.py`: follow/like/save/comment endpoints with mocked recipe/user checks.

## Deployment
- Docker image and Helm chart are provided for deployment.
- Health check: `GET /health`.
- Metrics: `GET /metrics` (Prometheus format).

## Troubleshooting
- Recipe/user service unreachable: verify `RECIPE_SERVICE_URL` and `USER_SERVICE_URL`.
- JWT errors: verify `JWT_SECRET` and `JWT_ALGORITHM`.
- Database connection errors: verify `DATABASE_URL` and Postgres container status.
