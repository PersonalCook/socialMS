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
