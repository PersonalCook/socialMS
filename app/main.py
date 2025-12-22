from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .routers import comments, follow, likes, saved
from .database import engine
from . import models

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
from .metrics import (
    num_requests,
    num_errors,
    request_latency,
    requests_in_progress
)

app = FastAPI(title="Social Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

app.include_router(comments.router)
app.include_router(follow.router)
app.include_router(likes.router)
app.include_router(saved.router)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    method = request.method
    endpoint = request.url.path

    requests_in_progress.inc()
    start_time = time.time()

    try:
        response = await call_next(request)
        status_code = response.status_code
        duration = time.time() - start_time

        num_requests.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

        if status_code >= 400:
            num_errors.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

        request_latency.labels(method=method, endpoint=endpoint).observe(duration)

        return response
    finally:
        requests_in_progress.dec()

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
 

@app.get("/")
def root():
    return {"msg": "Social Service running in Docker!"}


@app.get("/health")
def health():
    return {"status": "ok"}
