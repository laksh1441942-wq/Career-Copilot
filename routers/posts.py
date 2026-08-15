from typing import Annotated

from fastapi import Depends, status, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schema import PostCreate, PostResponse, PostUpdate

router = APIRouter()



@router.get("", response_model=list[PostResponse] )
async def get_posts(db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts


@router.get("/{post_id}", response_model=PostResponse)
async def get_posts(post_id : int, db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Post not found")

@router.put("/{post_id}", response_model=PostResponse)
async def update_posts_full(post_id : int, post_data : PostCreate, db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post_data.user_id != post.user_id:
        result = await db.execute(
            select(models.User).where(models.User.id == post_data.user_id)
        )
        user = result.scalars().first()
    
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    post.content = post_data.user_id
    post.title = post_data.title
    post.user_id = post_data.user_id

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post

@router.patch("/{post_id}", response_model=PostResponse)
async def update_posts_partial(post_id : int, post_data : PostUpdate, db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Post not found")

    update_data = post_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post

@router.delete("/{post_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id : int, db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
         raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Post not found")
    db.delete(post)
    await db.commit()
    return 
   
