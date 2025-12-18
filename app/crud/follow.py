from sqlalchemy.orm import Session
from .. import models, schemas
from typing import Optional


def follow_user(db:Session, follower_id:int, following_id:int):

    db_follow = models.Follow(
        follower_id=follower_id,
        following_id=following_id
    )
    db.add(db_follow)
    db.commit()
    db.refresh(db_follow)

    return db_follow

def get_follow(db:Session, follower_id:int, following_id:int) -> Optional[models.Follow]:
    follow = db.query(models.Follow).filter(models.Follow.follower_id == follower_id,
                                            models.Follow.following_id == following_id).first()
    return follow if follow else None

def get_followers(db:Session, user_id:int):
    return db.query(models.Follow).filter(models.Follow.following_id == user_id).all()

def get_following(db:Session, user_id:int):
    return db.query(models.Follow).filter(models.Follow.follower_id == user_id).all()

def unfollow_user(db:Session, follower_id:int, following_id:int):
    follow = get_follow(db, follower_id, following_id)
    if not follow:
        return None
    db.delete(follow)
    db.commit()
    return True

