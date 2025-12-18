import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import SessionLocal
import httpx
from .. import schemas
from ..crud.follow import follow_user, get_follow, get_followers, get_following, unfollow_user
from ..utils.auth import get_current_user_id

router = APIRouter(prefix="/follows", tags=["Follows"])

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL")

if not USER_SERVICE_URL:
    raise RuntimeError("USER_SERVICE_URL must be set in the environment")



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{following_id}", response_model=schemas.Follow, status_code=status.HTTP_201_CREATED)
async def create_follow(following_id: int, 
                        follower_id: int = Depends(get_current_user_id), 
                        db: Session = Depends(get_db)):

    if following_id == follower_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    existing = get_follow(db, follower_id=follower_id, following_id=following_id)
    if existing:
        raise HTTPException(status_code=400, detail="Already following this user")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/{following_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="User to follow not found")
        
    
    follow = follow_user(db, follower_id=follower_id, following_id=following_id)

    
    return follow

@router.delete("/{following_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_follow(following_id: int, follower_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):

    existing = get_follow(db, follower_id=follower_id, following_id=following_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Follow relationship not found")


    unfollow_user(db, follower_id=follower_id, following_id=following_id)

    return None

@router.get("/followers/me", response_model=list[schemas.Follow])
def get_my_followers(follower_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):

    followers = get_followers(db, user_id=follower_id)

    return followers

@router.get("/following/me", response_model=list[schemas.Follow])
def get_my_following(follower_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):

    following = get_following(db, user_id=follower_id)

    return following

@router.get("/followers/{user_id}", response_model=list[schemas.Follow])
def get_user_followers(user_id: int, db: Session = Depends(get_db)):

    followers = get_followers(db, user_id=user_id)

    return followers

@router.get("/following/{user_id}", response_model=list[schemas.Follow])
def get_user_following(user_id: int, db: Session = Depends(get_db)):

    following = get_following(db, user_id=user_id)

    return following






