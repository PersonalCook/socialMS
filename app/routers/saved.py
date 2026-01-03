import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import SessionLocal
import httpx
from .. import schemas, models
from ..crud.saved import save_recipe, get_saved, get_saved_for_user, unsave_recipe, get_saved_by_user_and_recipe
from ..utils.auth import get_current_user_id
from ..metrics import saved_items_total

router = APIRouter(prefix="/saved", tags=["Saved"])

EXAMPLE_SAVED = {
    "saved_id": 1,
    "user_id": 2,
    "recipe_id": 10,
    "created_at": "2025-01-01T12:00:00",
}

ERROR_400 = {
    "model": schemas.ErrorResponse,
    "description": "Bad request",
    "content": {"application/json": {"example": {"detail": "Recipe already saved"}}},
}
ERROR_401 = {
    "model": schemas.ErrorResponse,
    "description": "Unauthorized",
    "content": {"application/json": {"example": {"detail": "Invalid or expired token"}}},
}
ERROR_403 = {
    "model": schemas.ErrorResponse,
    "description": "Forbidden",
    "content": {"application/json": {"example": {"detail": "You can only unsave your own saved recipes"}}},
}
ERROR_404 = {
    "model": schemas.ErrorResponse,
    "description": "Not found",
    "content": {"application/json": {"example": {"detail": "Saved recipe not found"}}},
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

async def recipe_exists(recipe_id: int) -> bool:
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(f"{RECIPE_SERVICE_URL}/{recipe_id}")
        if r.status_code == 200:
            return True
        if r.status_code == 404:
            return False
        return True

@router.post(
    "/{recipe_id}",
    response_model=schemas.SavedRecipe,
    status_code=status.HTTP_201_CREATED,
    summary="Save recipe",
    responses={
        201: {"description": "Created", "content": {"application/json": {"example": EXAMPLE_SAVED}}},
        400: ERROR_400,
        401: ERROR_401,
        404: ERROR_404,
        422: {"description": "Validation error"},
        502: ERROR_502,
    },
)
async def create_saved(recipe_id: int, 
                       user_id: int = Depends(get_current_user_id), 
                       db: Session = Depends(get_db)):
    status_ = "success"
    action = "save"
    try:
        existing = get_saved_by_user_and_recipe(db, user_id=user_id, recipe_id=recipe_id)
        if existing:
            status_ ="error"
            raise HTTPException(status_code=400, detail="Recipe already saved")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RECIPE_SERVICE_URL}/{recipe_id}")
            if response.status_code != 200:
                status_ ="error"
                raise HTTPException(status_code=404, detail="Recipe not found")
        

        new_saved = save_recipe(db=db, user_id=user_id, recipe_id=recipe_id)  
        return new_saved
    except HTTPException:
        status_ = "error"
        raise
    except Exception as e:
        status_ = "error"
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        saved_items_total.labels(source="api", action=action, status=status_).inc()  


@router.get(
    "/my",
    response_model=list[schemas.SavedRecipe],
    summary="List my saved recipes",
    responses={
        200: {"description": "OK", "content": {"application/json": {"example": [EXAMPLE_SAVED]}}},
        401: ERROR_401,
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
async def get_saved_recipes(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    saved_recipes = get_saved_for_user(db, user_id=user_id)

    stale = []
    for s in saved_recipes:
        ok = await recipe_exists(s.recipe_id)
        if not ok:
            stale.append(s)

    if stale:
        for s in stale:
            db.delete(s)
        db.commit()

        saved_recipes = get_saved_for_user(db, user_id=user_id)

    return saved_recipes


@router.get(
    "/recipe/{recipe_id}/me",
    response_model=schemas.SavedRecipe | None,
    summary="Get my saved entry for recipe",
    responses={
        200: {"description": "OK", "content": {"application/json": {"example": EXAMPLE_SAVED}}},
        401: ERROR_401,
        422: {"description": "Validation error"},
        500: {"model": schemas.ErrorResponse, "description": "Internal error"},
    },
)
async def get_my_saved_for_recipe(
    recipe_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    saved = get_saved_by_user_and_recipe(db, user_id=user_id, recipe_id=recipe_id)
    if not saved:
        return None

    ok = await recipe_exists(recipe_id)
    if not ok:
        db.delete(saved)
        db.commit()
        return None

    return saved
@router.delete(
    "/{saved_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unsave recipe",
    responses={
        204: {"description": "Deleted"},
        401: ERROR_401,
        403: ERROR_403,
        404: ERROR_404,
        422: {"description": "Validation error"},
        502: ERROR_502,
    },
)
def delete_saved(saved_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    status_ = "success"
    action = "unsave"
    try:
        saved = get_saved(db, saved_id=saved_id)

        if not saved:
            status_ = "error"
            raise HTTPException(status_code=404, detail="Saved recipe not found")
        
        if saved.user_id != user_id:
            status_ = "error"
            raise HTTPException(403, "You can only unsave your own saved recipes")
        
        unsave_recipe(db, saved_id=saved_id)

        return None
    except HTTPException:
        status_ = "error"
        raise
    except Exception as e:
        status_ = "error"
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        saved_items_total.labels(source="api", action=action, status=status_).inc()
