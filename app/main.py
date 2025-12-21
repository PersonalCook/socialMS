from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import comments, follow, likes, saved
from .database import engine
from . import models

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


@app.get("/")
def root():
    return {"msg": "Social Service running in Docker!"}


@app.get("/health")
def health():
    return {"status": "ok"}
