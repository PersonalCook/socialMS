from sqlalchemy.orm import Session
from .. import models, schemas
from typing import Optional


def create_like(db: Session, user_id: int, recipe_id: int):
    db_like = models.Like(
        recipe_id=recipe_id,
        user_id=user_id
    )

    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like


def get_like(db: Session, like_id: int):
    like = db.query(models.Like).filter(models.Like.like_id == like_id).first() 
    return like if like else None

def get_like_by_user_and_recipe(db: Session, user_id: int, recipe_id: int):
    return (
        db.query(models.Like)
        .filter(models.Like.user_id == user_id, models.Like.recipe_id == recipe_id)
        .first()
    )

def get_likes_for_recipe(db: Session, recipe_id: int):
    return (
        db.query(models.Like)
        .filter(models.Like.recipe_id == recipe_id)
        .order_by(models.Like.created_at.asc())
        .all()
    )

def delete_like(db: Session, like_id:int):
    like = db.query(models.Like).filter(models.Like.like_id == like_id).first()
    if not like:
        return None
    db.delete(like)
    db.commit()
    return True


def count_likes(db: Session, recipe_id: int):
    return db.query(models.Like).filter(models.Like.recipe_id == recipe_id).count()
