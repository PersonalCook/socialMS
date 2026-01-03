# socialMS

Social service for PersonalCook.

---

## Overview
SocialMS handles follows, likes, saved recipes, and comments. It stores social data in PostgreSQL and validates recipe/user existence via upstream services.

---

## Architecture

- **FastAPI** application
- **PostgreSQL** for persistence
- **JWT-based auth** 
- **HTTP-based integration** with user and recipe services
- **Prometheus / Grafana** for metrics and monitoring
- **EFK stack (Fluent Bit, Elasticsearch, Kibana)** for centralized logging

---

## Configuration

The application configuration is fully separated from the implementation and is provided via multiple sources:

1. **Kubernetes ConfigMap**
   - Non-sensitive configuration injected as environment variables (and optionally as a mounted config file).
2. **Kubernetes Secrets**
   - Sensitive values such as JWT secret and database url.
3. **Helm values**
   - All configuration values are parameterized via Helm `values.yaml` files.

---

## Environment Variables

| Variable            | Description                                      |
| ------------------- | ------------------------------------------------ |
| DATABASE_URL        | PostgreSQL connection string                     |
| JWT_SECRET          | Secret used to sign and verify JWT tokens        |
| JWT_ALGORITHM       | JWT algorithm (default: HS256)                   |
| USER_SERVICE_URL    | Base URL of the user service                     |
| RECIPE_SERVICE_URL  | Base URL of the recipe service                   |

---

## Local development

Local development is performed using Docker Compose.

- Configuration via `.env` file (see `.env.example`)
- API available at: `http://localhost:8003`
- PostgreSQL exposed on: `localhost:5434`

Steps:

1. Create Docker network `personalcook-net`
2. Copy `.env.example` to `.env`
3. Run `docker compose up --build`

---

## Kubernetes

The service is deployed to Kubernetes using a Helm chart.

- Configuration via Helm values, ConfigMaps, and Secrets
- API exposed through the Ingress reverse proxy: http://134.112.152.8/api/social/
- Observability via `/metrics` endpoint

Separate Helm values files are used:

- `values-dev.yaml`
- `values-prod.yaml`

Example deployment:

helm upgrade --install social-service . -n personalcook -f values-prod.yaml

---

## Observability & Logging

The Social Service is integrates with a centralized logging and monitoring stack.

### Logging (EFK stack)

Application logs are written to stdout and collected at the Kubernetes level using:

- **Fluent Bit** – log collection and forwarding
- **Elasticsearch** – centralized log storage and indexing
- **Kibana** – log visualization and analysis

### Metrics & Monitoring

The service exposes Prometheus-compatible metrics at: /metrics

Metrics are scraped using:

- **Prometheus Operator** via a `ServiceMonitor`
- Visualized in **Grafana**

#### Exposed metrics

- **`http_requests_total`** _(Counter)_  
  Total number of HTTP requests.  
  **Labels:** `method`, `endpoint`, `status_code`

- **`http_request_errors_total`** _(Counter)_  
  Total number of failed HTTP requests (error responses).  
  **Labels:** `method`, `endpoint`, `status_code`

- **`http_request_latency_seconds`** _(Histogram)_  
  HTTP request latency distribution (seconds).  
  **Labels:** `method`, `endpoint`

- **`http_requests_in_progress`** _(Gauge)_  
  Number of HTTP requests currently being processed.

- **`likes_total`** (Counter)  
  Total number of likes actions.  
  Labels: `action`, `source`, `status`

- **`comments_total`** (Counter)  
  Total number of created comments.  
  Labels: `source`, `status`

- **`follows_total`** (Counter)  
  Total number of follow actions.  
  Labels: `action`, `source`, `status`

- **`saved_items_total`** (Counter)  
  Total number of saved-items actions (save/unsave).  
  Labels: `action`, `source`, `status`

---

## Dependencies
- recipe service at RECIPE_SERVICE_URL (default http://recipe_service:8000/recipes)
- user service at USER_SERVICE_URL (default http://user_service:8000/users)

---
## API Docs

- Swagger UI: http://134.112.152.8/api/social/docs
- ReDoc: http://134.112.152.8/api/social/redoc
- OpenAPI JSON: http://134.112.152.8/api/social/openapi.json

---

## Testing
Run tests locally:
```
pytest
```

---

## CI
This repo runs two GitHub Actions jobs:
- `test`: installs requirements and runs `pytest`
- `container`: builds the Docker image, starts Postgres, runs the container, and hits `/` for a smoke test

Tests (files and intent):
- `tests/test_social_routes.py`: follow/like/save/comment endpoints with mocked recipe/user checks.

---

## Troubleshooting
- Recipe/user service unreachable: verify `RECIPE_SERVICE_URL` and `USER_SERVICE_URL`.
- JWT errors: verify `JWT_SECRET` and `JWT_ALGORITHM`.
- Database connection errors: verify `DATABASE_URL` and Postgres container status.
