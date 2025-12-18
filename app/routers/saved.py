import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import SessionLocal
import httpx
from .. import schemas, models
from ..crud.saved import save_recipe, get_saved, get_saved_for_user, unsave_recipe, get_saved_by_user_and_recipe
from ..utils.auth import get_current_user_id

router = APIRouter(prefix="/saved", tags=["Saved"])

RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL")

if not RECIPE_SERVICE_URL:
    raise RuntimeError("RECIPE_SERVICE_URL must be set in the environment")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{recipe_id}", response_model=schemas.SavedRecipe, status_code=status.HTTP_201_CREATED)
async def create_saved(recipe_id: int, 
                       user_id: int = Depends(get_current_user_id), 
                       db: Session = Depends(get_db)):
    # prevent duplicate saved entries
    existing = get_saved_by_user_and_recipe(db, user_id=user_id, recipe_id=recipe_id)
    if existing:
        raise HTTPException(status_code=400, detail="Recipe already saved")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RECIPE_SERVICE_URL}/{recipe_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Recipe not found")
    

    new_saved = save_recipe(db=db, user_id=user_id, recipe_id=recipe_id)  
    return new_saved  


@router.get("/my", response_model=list[schemas.SavedRecipe])
def get_saved_recipes(user_id: int  = Depends(get_current_user_id), db: Session = Depends(get_db)):
    saved_recipes = get_saved_for_user(db, user_id=user_id)

    return saved_recipes


@router.get("/recipe/{recipe_id}/me", response_model=schemas.SavedRecipe | None)
def get_my_saved_for_recipe(
    recipe_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    saved = get_saved_by_user_and_recipe(db, user_id=user_id, recipe_id=recipe_id)
    return saved

@router.delete("/{saved_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved(saved_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    saved = get_saved(db, saved_id=saved_id)

    if not saved:
        raise HTTPException(status_code=404, detail="Saved recipe not found")
    
    if saved.user_id != user_id:
        raise HTTPException(403, "You can only unsave your own saved recipes")
    
    unsave_recipe(db, saved_id=saved_id)

    return None
