import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import SessionLocal
import httpx
from .. import schemas, models
from ..crud.likes import (
    create_like as create_like_crud,
    get_like,
    delete_like as delete_like_crud,
    get_likes_for_recipe,
    count_likes,
    get_like_by_user_and_recipe,
)
from ..utils.auth import get_current_user_id
from ..metrics import likes_total

router = APIRouter(prefix="/likes", tags=["Likes"])

EXAMPLE_LIKE = {
    "like_id": 1,
    "recipe_id": 10,
    "user_id": 2,
    "created_at": "2025-01-01T12:00:00",
}

ERROR_400 = {
    "model": schemas.ErrorResponse,
    "description": "Bad request",
    "content": {"application/json": {"example": {"detail": "Recipe already liked"}}},
}
ERROR_401 = {
    "model": schemas.ErrorResponse,
    "description": "Unauthorized",
    "content": {"application/json": {"example": {"detail": "Invalid or expired token"}}},
}
ERROR_403 = {
    "model": schemas.ErrorResponse,
    "description": "Forbidden",
    "content": {"application/json": {"example": {"detail": "You can delete only your own likes"}}},
}
ERROR_404 = {
    "model": schemas.ErrorResponse,
    "description": "Not found",
    "content": {"application/json": {"example": {"detail": "Like not found"}}},
}
ERROR_502 = {
    "model": schemas.ErrorResponse,
    "description": "Upstream error",
    "content": {"application/json": {"example": {"detail": "Recipe service unavailable"}}},
}

RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL")

if not RECIPE_SERVICE_URL:
    raise RuntimeError("RECIPE_SERVICE_URL must be set in the environment")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/{recipe_id}",
    response_model=schemas.Like,
    status_code=status.HTTP_201_CREATED,
    summary="Like recipe",
    responses={
        201: {"description": "Created", "content": {"application/json": {"example": EXAMPLE_LIKE}}},
        400: ERROR_400,
        401: ERROR_401,
        404: ERROR_404,
        422: {"description": "Validation error"},
        502: ERROR_502,
    },
)
async def create_like(recipe_id: int, 
                      user_id: int = Depends(get_current_user_id), 
                      db: Session = Depends(get_db)):
    status_ = "success"
    action = "like"
    try:
        existing = get_like_by_user_and_recipe(db, user_id=user_id, recipe_id=recipe_id)
        if existing:
            status_ ="error"
            raise HTTPException(status_code=400, detail="Recipe already liked")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RECIPE_SERVICE_URL}/{recipe_id}")
            if response.status_code != 200:
                status_ ="error"
                raise HTTPException(status_code=404, detail="Recipe not found")

        new_like = create_like_crud(db=db, user_id=user_id, recipe_id=recipe_id)
        return new_like
    except HTTPException:
        status_ = "error"
        raise
    except Exception as e:
        status_ = "error"
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        likes_total.labels(source="api", action=action, status=status_).inc()

@router.get(
    "/like/{like_id}",
    response_model=schemas.Like,
    summary="Get like by id",
    responses={
        200: {"description": "OK", "content": {"application/json": {"example": EXAMPLE_LIKE}}},
        404: ERROR_404,
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def read_like(like_id: int, db: Session = Depends(get_db)):
    like = get_like(db, like_id=like_id)
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    return like


@router.get(
    "/recipe/{recipe_id}",
    response_model=list[schemas.Like],
    summary="List likes for recipe",
    responses={
        200: {"description": "OK", "content": {"application/json": {"example": [EXAMPLE_LIKE]}}},
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def get_all_likes(recipe_id: int, db: Session = Depends(get_db)):
    all_likes = get_likes_for_recipe(db, recipe_id=recipe_id)

    return all_likes


@router.get(
    "/recipe/{recipe_id}/me",
    response_model=schemas.Like | None,
    summary="Get my like for recipe",
    responses={
        200: {"description": "OK", "content": {"application/json": {"example": EXAMPLE_LIKE}}},
        401: ERROR_401,
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def get_my_like_for_recipe(
    recipe_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    like = get_like_by_user_and_recipe(db, user_id=user_id, recipe_id=recipe_id)
    return like

@router.delete(
    "/{like_id}",
    status_code=204,
    summary="Remove like",
    responses={
        204: {"description": "Deleted"},
        401: ERROR_401,
        403: ERROR_403,
        404: ERROR_404,
        422: {"description": "Validation error"},
        502: ERROR_502,
    },
)
def delete_like(like_id: int,
                user_id: int  = Depends(get_current_user_id),
                db: Session = Depends(get_db)):
    
    status_ = "success"
    action = "unlike"
    try:

        like = get_like(db, like_id=like_id)

        if not like:
            status_ ="error"
            raise HTTPException(status_code=404, detail="Like not found")
        
        if like.user_id != user_id:
            status_ ="error"
            raise HTTPException(status_code=403, detail="You can delete only your own likes")
        
        success = delete_like_crud(db, like_id)

        if not success:
            status_ ="error"
            raise HTTPException(status_code=404, detail="Like not deleted")

        return None
    except HTTPException:
        status_ = "error"
        raise
    except Exception as e:
        status_ = "error"
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        likes_total.labels(source="api", action=action, status=status_).inc()

@router.get(
    "/count/{recipe_id}",
    response_model=schemas.LikeCountResponse,
    summary="Count likes for recipe",
    responses={
        200: {
            "description": "OK",
            "content": {"application/json": {"example": {"recipe_id": 10, "like_count": 3}}},
        },
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def count_likes_endpoint(recipe_id: int, db: Session = Depends(get_db)):
    count = count_likes(db, recipe_id=recipe_id)
    return {"recipe_id": recipe_id, "like_count": count}
    
