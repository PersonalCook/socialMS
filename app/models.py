from sqlalchemy import Column, Integer, Text, TIMESTAMP
from .database import Base
from sqlalchemy.sql import func


class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Like(Base):
    __tablename__ = "likes"

    like_id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Follow(Base):
    __tablename__ = "follows"
    follower_id = Column(Integer, primary_key=True)
    following_id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class SavedRecipe(Base):
    __tablename__ = "saved_recipes"

    saved_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    recipe_id = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
