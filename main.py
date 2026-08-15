from contextlib import asynccontextmanager
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler
)

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarHTTPSException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from typing import Annotated

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db, Base, engine
from schema import PostCreate, PostResponse

from routers import users , posts

@asynccontextmanager
async def lifespan(_app: FastAPI):
    #startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    #shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media" , StaticFiles(directory="media"), name="media")

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])

@app.get("/", name="home")
@app.get("/posts", name="posts")
async def home(request: Request, db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request, "home.html",
        {"title": "home",
        "posts": posts 
    })

@app.get("/posts/{post_id}", include_in_schema=False)
async def your_post(request: Request, post_id : int, db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post)
                              .options(selectinload(models.Post.author))
                              .where(models.Post.id == post_id)
                              )
    post = result.scalars().first() 
    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post" : post, "title" : title}
        )
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Post not found")



@app.get("users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_post_page(request : Request, user_id : int, db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user :
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not Found"
        )
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts" : posts, "user" : user, "title" : f"{user.username}'s Posts"},
    )

@app.post("/api/post", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post : PostCreate, db : Annotated[AsyncSession, Depends(get_db)]):
    result = await  db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not Found"
        )
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = post.user_id,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])
    return new_post

@app.exception_handler(StarHTTPSException)
async def gen_exception_handler(request: Request, exception: StarHTTPSException):
    
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)

    message = (
            exception.detail
            if exception.detail
            else "An error has occured"
        )
    return templates.TemplateResponse(
                request,
                "error.html",
                {
                    "status_code" : exception.status_code,
                    "message" : message
                },
                status_code = exception.status_code
            )
        

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request : Request, exception : RequestValidationError):

    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)
    
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code" : status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message" : exception.errors(),
        },
        status_code= status.HTTP_422_UNPROCESSABLE_CONTENT
    )