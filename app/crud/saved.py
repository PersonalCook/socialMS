from sqlalchemy.orm import Session
from .. import models, schemas
from typing import Optional


def save_recipe(db: Session, user_id: int, recipe_id: int) -> dict:
    db_saved = models.SavedRecipe(
        user_id=user_id,
        recipe_id=recipe_id
    )
    db.add(db_saved)
    db.commit()
    db.refresh(db_saved)

    return db_saved

def get_saved(db: Session, saved_id: int):
    saved = db.query(models.SavedRecipe).filter(models.SavedRecipe.saved_id == saved_id).first()

    return saved if saved else None

def get_saved_by_user_and_recipe(db: Session, user_id: int, recipe_id: int):
    return (
        db.query(models.SavedRecipe)
        .filter(models.SavedRecipe.user_id == user_id, models.SavedRecipe.recipe_id == recipe_id)
        .first()
    )


def get_saved_for_user(db: Session, user_id: int):
    return (
        db.query(models.SavedRecipe)
        .filter(models.SavedRecipe.user_id == user_id)
        .order_by(models.SavedRecipe.created_at.desc())
        .all()
    )

def unsave_recipe(db: Session, saved_id: int):
    saved = db.query(models.SavedRecipe).filter(models.SavedRecipe.saved_id == saved_id).first()
    if not saved:
        return None
    db.delete(saved)
    db.commit()
    return True
