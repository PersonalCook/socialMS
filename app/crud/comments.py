from sqlalchemy.orm import Session
from .. import models, schemas
from typing import Optional


def create_comment(db: Session, comment: schemas.CommentCreate, user_id: int, recipe_id: int) -> dict:
    db_comment = models.Comment(
        content=comment.content,
        user_id=user_id,
        recipe_id=recipe_id
    )

    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comment(db: Session, comment_id: int) -> Optional[dict]:
    comment = db.query(models.Comment).filter(models.Comment.comment_id == comment_id).first() 
    return comment if comment else None

def get_comments_for_recipe(db: Session, recipe_id: int):
    return (
        db.query(models.Comment)
        .filter(models.Comment.recipe_id == recipe_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )

def delete_comment(db: Session, comment_id:int):
    comment = db.query(models.Comment).filter(models.Comment.comment_id == comment_id).first()
    if not comment:
        return None
    db.delete(comment)
    db.commit()
    return True
    
def count_comments(db: Session, recipe_id: int):
    return db.query(models.Comment).filter(models.Comment.recipe_id == recipe_id).count()

