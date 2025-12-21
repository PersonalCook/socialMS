CI overview

This repo runs two GitHub Actions jobs:
- test: installs requirements and runs `pytest`
- container: builds the Docker image, starts Postgres, runs the container, and hits `/` for a smoke test

Tests (files and intent):
- `tests/test_social_routes.py`: follow/like/save/comment endpoints with mocked recipe/user checks.
