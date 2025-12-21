import os

import httpx
import jwt


class _StubResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class _StubAsyncClient:
    def __init__(self, *args, **kwargs):
        self._response = _StubResponse()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *args, **kwargs):
        return self._response


def _auth_headers(user_id=1):
    token = jwt.encode(
        {"user_id": user_id},
        os.environ["JWT_SECRET"],
        algorithm=os.environ["JWT_ALGORITHM"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_follow_create_and_list(client, db_session, monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _StubAsyncClient)

    response = client.post("/follows/2", headers=_auth_headers(1))
    assert response.status_code == 201

    response = client.get("/follows/following/me", headers=_auth_headers(1))
    assert response.status_code == 200
    assert response.json()[0]["following_id"] == 2


def test_like_create_and_count(client, db_session, monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _StubAsyncClient)

    response = client.post("/likes/10", headers=_auth_headers(1))
    assert response.status_code == 201

    response = client.get("/likes/count/10")
    assert response.status_code == 200
    assert response.json()["like_count"] == 1


def test_saved_create_and_list(client, db_session, monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _StubAsyncClient)

    response = client.post("/saved/5", headers=_auth_headers(1))
    assert response.status_code == 201

    response = client.get("/saved/my", headers=_auth_headers(1))
    assert response.status_code == 200
    assert response.json()[0]["recipe_id"] == 5


def test_comment_create_and_count(client, db_session, monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _StubAsyncClient)

    response = client.post(
        "/comments/3",
        json={"content": "Nice recipe"},
        headers=_auth_headers(1),
    )
    assert response.status_code == 201

    response = client.get("/comments/count/3")
    assert response.status_code == 200
    assert response.json()["comment_count"] == 1
