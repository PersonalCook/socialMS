import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import SessionLocal
import httpx
from .. import schemas
from ..crud.comments import create_comment as create_comment_crud, get_comment, delete_comment as delete_comment_crud, get_comments_for_recipe, count_comments
from ..utils.auth import get_current_user_id
from ..metrics import comments_total

router = APIRouter(prefix="/comments", tags=["Comments"])

RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL")

if not RECIPE_SERVICE_URL:
    raise RuntimeError("RECIPE_SERVICE_URL must be set in the environment")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{recipe_id}", response_model=schemas.Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment: schemas.CommentCreate, 
    recipe_id: int,  
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

@router.get("/comment/{comment_id}", response_model=schemas.Comment)
def read_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = get_comment(db, comment_id=comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.get("/recipe/{recipe_id}", response_model=list[schemas.Comment])
def get_all_comments(recipe_id: int, db: Session = Depends(get_db)):
    all_comments = get_comments_for_recipe(db, recipe_id=recipe_id)

    return all_comments

@router.delete("/{comment_id}", status_code=204)
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

@router.get("/count/{recipe_id}")
def count_comments_endpoint(recipe_id: int, db: Session = Depends(get_db)):
    count = count_comments(db, recipe_id=recipe_id)
    return {"recipe_id": recipe_id, "comment_count": count}
    