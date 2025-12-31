# socialMS

Social service for PersonalCook.

## Local dev
1. docker network create personalcook-net
2. copy .env.example .env
3. docker compose up --build

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

## CI
This repo runs two GitHub Actions jobs:
- test: installs requirements and runs `pytest`
- container: builds the Docker image, starts Postgres, runs the container, and hits `/` for a smoke test

Tests (files and intent):
- `tests/test_social_routes.py`: follow/like/save/comment endpoints with mocked recipe/user checks.
