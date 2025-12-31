import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import SessionLocal
import httpx
from .. import schemas
from ..crud.follow import follow_user, get_follow, get_followers, get_following, unfollow_user
from ..utils.auth import get_current_user_id
from ..metrics import follows_total

router = APIRouter(prefix="/follows", tags=["Follows"])

EXAMPLE_FOLLOW = {
    "follower_id": 1,
    "following_id": 2,
    "created_at": "2025-01-01T12:00:00",
}

ERROR_400 = {
    "model": schemas.ErrorResponse,
    "description": "Bad request",
    "content": {"application/json": {"example": {"detail": "Already following this user"}}},
}
ERROR_401 = {
    "model": schemas.ErrorResponse,
    "description": "Unauthorized",
    "content": {"application/json": {"example": {"detail": "Invalid or expired token"}}},
}
ERROR_404 = {
    "model": schemas.ErrorResponse,
    "description": "Not found",
    "content": {"application/json": {"example": {"detail": "User to follow not found"}}},
}
ERROR_502 = {
    "model": schemas.ErrorResponse,
    "description": "Upstream error",
    "content": {"application/json": {"example": {"detail": "User service unavailable"}}},
}

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL")

if not USER_SERVICE_URL:
    raise RuntimeError("USER_SERVICE_URL must be set in the environment")



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/{following_id}",
    response_model=schemas.Follow,
    status_code=status.HTTP_201_CREATED,
    summary="Follow user",
    responses={
        201: {"description": "Created", "content": {"application/json": {"example": EXAMPLE_FOLLOW}}},
        400: ERROR_400,
        401: ERROR_401,
        404: ERROR_404,
        422: {"description": "Validation error"},
        502: ERROR_502,
    },
)
async def create_follow(following_id: int, 
                        follower_id: int = Depends(get_current_user_id), 
                        db: Session = Depends(get_db)):

    status_ = "success"
    action = "follow"
    try:
        if following_id == follower_id:
            status_ ="error"
            raise HTTPException(status_code=400, detail="Cannot follow yourself")
        
        existing = get_follow(db, follower_id=follower_id, following_id=following_id)
        if existing:
            status_ ="error"
            raise HTTPException(status_code=400, detail="Already following this user")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{USER_SERVICE_URL}/{following_id}")
            if response.status_code != 200:
                status_ ="error"
                raise HTTPException(status_code=404, detail="User to follow not found")
            
        
        follow = follow_user(db, follower_id=follower_id, following_id=following_id)

        
        return follow
    except HTTPException:
        status_ = "error"
        raise

    except Exception as e:
        status_ = "error"
        raise HTTPException(status_code=502, detail=str(e))

    finally:
        follows_total.labels(
            source="api",
            action=action,
            status=status_
        ).inc()

@router.delete(
    "/{following_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow user",
    responses={
        204: {"description": "Deleted"},
        401: ERROR_401,
        404: ERROR_404,
        422: {"description": "Validation error"},
        502: ERROR_502,
    },
)
def delete_follow(following_id: int, follower_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    status_ = "success"
    action = "unfollow"
    try:
        existing = get_follow(db, follower_id=follower_id, following_id=following_id)
        if not existing:
            status_ ="error"
            raise HTTPException(status_code=404, detail="Follow relationship not found")


        unfollow_user(db, follower_id=follower_id, following_id=following_id)

        return None
    except HTTPException:
        status_ = "error"
        raise
    except Exception as e:
        status_ = "error"
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        follows_total.labels(
            source="api",
            action=action,
            status=status_
        ).inc()

@router.get(
    "/followers/me",
    response_model=list[schemas.Follow],
    summary="List my followers",
    responses={
        200: {"description": "OK", "content": {"application/json": {"example": [EXAMPLE_FOLLOW]}}},
        401: ERROR_401,
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def get_my_followers(follower_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):

    followers = get_followers(db, user_id=follower_id)

    return followers

@router.get(
    "/following/me",
    response_model=list[schemas.Follow],
    summary="List users I follow",
    responses={
        200: {"description": "OK", "content": {"application/json": {"example": [EXAMPLE_FOLLOW]}}},
        401: ERROR_401,
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def get_my_following(follower_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):

    following = get_following(db, user_id=follower_id)

    return following

@router.get(
    "/followers/{user_id}",
    response_model=list[schemas.Follow],
    summary="List followers for a user",
    responses={
        200: {"description": "OK", "content": {"application/json": {"example": [EXAMPLE_FOLLOW]}}},
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def get_user_followers(user_id: int, db: Session = Depends(get_db)):

    followers = get_followers(db, user_id=user_id)

    return followers

@router.get(
    "/following/{user_id}",
    response_model=list[schemas.Follow],
    summary="List following for a user",
    responses={
        200: {"description": "OK", "content": {"application/json": {"example": [EXAMPLE_FOLLOW]}}},
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def get_user_following(user_id: int, db: Session = Depends(get_db)):

    following = get_following(db, user_id=user_id)

    return following






