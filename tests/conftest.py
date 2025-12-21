import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_ROOT_DIR = Path(__file__).resolve().parents[1]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

_TMP_DIR = Path(tempfile.mkdtemp(prefix="socialms-tests-"))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TMP_DIR / 'test.db'}")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("RECIPE_SERVICE_URL", "http://recipe-service.local/recipes")
os.environ.setdefault("USER_SERVICE_URL", "http://user-service.local/users")

from app import models  # noqa: E402
from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def db_session():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(models.Comment).delete()
        db.query(models.Like).delete()
        db.query(models.Follow).delete()
        db.query(models.SavedRecipe).delete()
        db.commit()
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    app.dependency_overrides = {}
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides = {}
