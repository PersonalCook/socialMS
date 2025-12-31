import os
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from ..database import SessionLocal
import httpx
from .. import schemas
from ..crud.comments import create_comment as create_comment_crud, get_comment, delete_comment as delete_comment_crud, get_comments_for_recipe, count_comments
from ..utils.auth import get_current_user_id
from ..metrics import comments_total

router = APIRouter(prefix="/comments", tags=["Comments"])

EXAMPLE_COMMENT = {
    "comment_id": 1,
    "recipe_id": 10,
    "user_id": 2,
    "content": "Great recipe!",
    "created_at": "2025-01-01T12:00:00",
}

ERROR_401 = {
    "model": schemas.ErrorResponse,
    "description": "Unauthorized",
    "content": {"application/json": {"example": {"detail": "Invalid or expired token"}}},
}
ERROR_403 = {
    "model": schemas.ErrorResponse,
    "description": "Forbidden",
    "content": {"application/json": {"example": {"detail": "You can delete only your own comments"}}},
}
ERROR_404 = {
    "model": schemas.ErrorResponse,
    "description": "Not found",
    "content": {"application/json": {"example": {"detail": "Comment not found"}}},
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
    response_model=schemas.Comment,
    status_code=status.HTTP_201_CREATED,
    summary="Create comment",
    responses={
        201: {"description": "Created", "content": {"application/json": {"example": EXAMPLE_COMMENT}}},
        401: ERROR_401,
        404: ERROR_404,
        422: {"description": "Validation error"},
        502: ERROR_502,
    },
)
async def create_comment(
    recipe_id: int,
    comment: schemas.CommentCreate = Body(
        ...,
        examples={"example": {"value": {"content": "Great recipe!"}}},
    ),
    user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db),
):
    status_ = "success"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RECIPE_SERVICE_URL}/{recipe_id}")
            if response.status_code != 200:
                status_ = "error"
                raise HTTPException(status_code=404, detail="Recipe not found")

        new_comment = create_comment_crud(
            db=db,
            comment=comment,
            user_id=user_id,
            recipe_id=recipe_id,
        )
        return new_comment

    except HTTPException:
        status_ = "error"
        raise

    except Exception as e:
        status_ = "error"
        raise HTTPException(status_code=502, detail=str(e))

    finally:
        comments_total.labels(
            source="api",
            status=status_,
        ).inc()

@router.get(
    "/comment/{comment_id}",
    response_model=schemas.Comment,
    summary="Get comment by id",
    responses={
        200: {"description": "OK", "content": {"application/json": {"example": EXAMPLE_COMMENT}}},
        404: ERROR_404,
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def read_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = get_comment(db, comment_id=comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.get(
    "/recipe/{recipe_id}",
    response_model=list[schemas.Comment],
    summary="List comments for recipe",
    responses={
        200: {"description": "OK", "content": {"application/json": {"example": [EXAMPLE_COMMENT]}}},
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def get_all_comments(recipe_id: int, db: Session = Depends(get_db)):
    all_comments = get_comments_for_recipe(db, recipe_id=recipe_id)

    return all_comments

@router.delete(
    "/{comment_id}",
    status_code=204,
    summary="Delete comment",
    responses={
        204: {"description": "Deleted"},
        401: ERROR_401,
        403: ERROR_403,
        404: ERROR_404,
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def delete_comment(
    comment_id: int, 
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)):
    
    comment = get_comment(db, comment_id=comment_id)

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can delete only your own comments")
    
    delete_comment_crud(db, comment_id)

    return None

@router.get(
    "/count/{recipe_id}",
    response_model=schemas.CommentCountResponse,
    summary="Count comments for recipe",
    responses={
        200: {
            "description": "OK",
            "content": {"application/json": {"example": {"recipe_id": 10, "comment_count": 2}}},
        },
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
def count_comments_endpoint(recipe_id: int, db: Session = Depends(get_db)):
    count = count_comments(db, recipe_id=recipe_id)
    return {"recipe_id": recipe_id, "comment_count": count}
    
