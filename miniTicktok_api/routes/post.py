from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette import status
from typing import List, Optional
from miniTicktok_api.auth import get_current_user
from miniTicktok_api.external.mongodb import MongodbDatabase
from miniTicktok_api.models.post import Post, PostType
from miniTicktok_api.models.users import User, PublicUser
from miniTicktok_api.models.videos import VideoRecording
from miniTicktok_api.services import services
from miniTicktok_api.routes.utils import PaginatedList, ITEMS_PER_PAGE_DEFAULT

from pydantic import BaseModel, Field, HttpUrl
from uuid import uuid4


# =================== Router ==================== #


router = APIRouter(
    prefix='/feed_post',
    tags=['Feed Posts'],
    dependencies=[Depends(get_current_user)],
)

# =============== Response Models =============== #


class CreatePostRequest(BaseModel):

    title: Optional[str] = Field(
        description='The title of the video post.', max_length=40)

    video_uri: HttpUrl = Field(description='URI for the video recording.')

    location: Optional[str] = Field(
        max_length=50, description="Location of the video")

    post_type: PostType = Field(
        default=PostType.PUBLIC,
        description="Type of post public or private ."
    )


class PostDetails(Post):

    username: Optional[str] = Field(
        description='The username of the user.',
        max_length=30,
    )

# =============== Private Methods =============== #


def _get_post(post_id: UUID) -> Post:
    posts_collection = services.get(
        MongodbDatabase).database.get_collection('posts')
    post_data = posts_collection.find_one({"id":  post_id})

    if not post_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    post: Post = Post.parse_obj(post_data)

    return post


def _get_profile_data(user_id: UUID) -> PublicUser:
    '''retrive public profile of any specific user'''

    profile_collection = services.get(MongodbDatabase).database.get_collection('users')
    profile_data = profile_collection.find_one({"id":  user_id})
    profile:  PublicUser = PublicUser.parse_obj(profile_data)
    return profile


# ================== Endpoints ================== #


@router.get(
    path='/{post_id}',
    description='Get details about a specific post.',
    response_model=PostDetails,
)
async def get_post(post_id: UUID) -> PostDetails:
    post_data = _get_post(post_id)
    post: PostDetails = PostDetails.parse_obj(post_data)
    return post


@router.get(
    path='/profiles/me',
    description='Get all the posts by the authenticated user.',
    response_model=PaginatedList[PostDetails],
)
async def get_posts(page: int = 1, user: User = Depends(get_current_user)) -> PaginatedList[PostDetails]:
    posts: List[PostDetails] = []
    posts_collection = services.get(MongodbDatabase).database.get_collection('posts')

    skip = (page - 1) * ITEMS_PER_PAGE_DEFAULT
    post_count = posts_collection.count_documents({"from_user_id": user.id})

    posts_data = posts_collection \
        .find({"from_user_id": user.id}, sort=[('created_at', -1)]) \
        .skip(skip) \
        .limit(ITEMS_PER_PAGE_DEFAULT)

    for post_data in posts_data:
        post: PostDetails = PostDetails.parse_obj(post_data)
        post.username = user.username
        posts.append(post)

    return PaginatedList[PostDetails].create_list(
        items=posts,
        current_page=page,
        total_items=post_count,
        items_per_page=ITEMS_PER_PAGE_DEFAULT,
    )


@router.get(
    path='',
    description='Get feed of the authenticated user.',
    response_model=PaginatedList[PostDetails],
)
async def get_public_feed(page: int = 1) -> PaginatedList[PostDetails]:
    posts: List[PostDetails] = []
    posts_collection = services.get(MongodbDatabase).database.get_collection('posts')

    skip = (page - 1) * ITEMS_PER_PAGE_DEFAULT

    post_count = posts_collection.count_documents({"post_type": PostType.PUBLIC, })

    posts_data = posts_collection \
        .find({"post_type": PostType.PUBLIC, }, sort=[('created_at', -1)]) \
        .skip(skip) \
        .limit(ITEMS_PER_PAGE_DEFAULT)

    for post_data in posts_data:
        post: PostDetails = PostDetails.parse_obj(post_data)
        profile_data = _get_profile_data(post.from_user_id)
        post.username = profile_data.username
        posts.append(post)

    return PaginatedList[PostDetails].create_list(
        items=posts,
        current_page=page,
        total_items=post_count,
        items_per_page=ITEMS_PER_PAGE_DEFAULT,
    )


@router.post(
    path='',
    description='Create and post a feed-post.',
    response_model=Post,
)
async def create_post(request: CreatePostRequest, user: User = Depends(get_current_user)):

    post_collection = services.get(MongodbDatabase).database.get_collection('posts')

    post = Post(
        from_user_id=user.id,
        post_type=request.post_type,
        title=request.title,
        video_uri=request.video_uri,
        location=request.location,
    )

    post_collection.insert_one(post.dict())

    return post

# Note I know the goal was to to upload the video and metadata at the same request but
# I have separated the request for uploading video which will return the url
# the url which can be used to append in the feed post requests
# this makes the implementation alot cleaner and smooth although the video upload api can be appended here to achieve the intended goal
