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

router = APIRouter(prefix="/likes", tags=["Likes"])

RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL")

if not RECIPE_SERVICE_URL:
    raise RuntimeError("RECIPE_SERVICE_URL must be set in the environment")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{recipe_id}", response_model=schemas.Like, status_code=status.HTTP_201_CREATED)
async def create_like(recipe_id: int, 
                      user_id: int = Depends(get_current_user_id), 
                      db: Session = Depends(get_db)):

    # prevent duplicate likes by same user on same recipe
    existing = get_like_by_user_and_recipe(db, user_id=user_id, recipe_id=recipe_id)
    if existing:
        raise HTTPException(status_code=400, detail="Recipe already liked")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RECIPE_SERVICE_URL}/{recipe_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Recipe not found")

    new_like = create_like_crud(db=db, user_id=user_id, recipe_id=recipe_id)
    return new_like

@router.get("/like/{like_id}", response_model=schemas.Like)
def read_like(like_id: int, db: Session = Depends(get_db)):
    like = get_like(db, like_id=like_id)
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    return like


@router.get("/recipe/{recipe_id}", response_model=list[schemas.Like])
def get_all_likes(recipe_id: int, db: Session = Depends(get_db)):
    all_likes = get_likes_for_recipe(db, recipe_id=recipe_id)

    return all_likes


@router.get("/recipe/{recipe_id}/me", response_model=schemas.Like | None)
def get_my_like_for_recipe(
    recipe_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    like = get_like_by_user_and_recipe(db, user_id=user_id, recipe_id=recipe_id)
    return like

@router.delete("/{like_id}", status_code=204)
def delete_like(like_id: int,
                user_id: int  = Depends(get_current_user_id),
                db: Session = Depends(get_db)):
    
    like = get_like(db, like_id=like_id)

    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    if like.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can delete only your own likes")
    
    success = delete_like_crud(db, like_id)

    if not success:
        raise HTTPException(status_code=404, detail="Like not deleted")

    return None

@router.get("/count/{recipe_id}")
def count_likes_endpoint(recipe_id: int, db: Session = Depends(get_db)):
    count = count_likes(db, recipe_id=recipe_id)
    return {"recipe_id": recipe_id, "like_count": count}
    
