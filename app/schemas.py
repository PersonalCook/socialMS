from pydantic import BaseModel
from datetime import datetime


#Comments input
class CommentCreate(BaseModel):
    content: str

#Comments response schema
class Comment(BaseModel):
    comment_id: int
    recipe_id: int
    user_id: int
    content: str
    created_at: datetime

    class Config:
        orm_mode = True #da pydantic lahko pretvori iz sqlalchemy modela v pydantic model

#Likes response schema
class Like(BaseModel):
    like_id: int
    recipe_id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

#Saved recipes response schema
class SavedRecipe(BaseModel):
    saved_id: int
    user_id: int
    recipe_id: int
    created_at: datetime

    class Config:
        orm_mode = True

#Follow response scheme
class Follow(BaseModel):
    follower_id: int
    following_id: int
    created_at: datetime

    class Config:
        orm_mode = True 

