from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from enum import Enum


class PostType(str, Enum):
    """The Type of post."""

    PRIVATE = 'private'
    PUBLIC = 'public'


class Post(BaseModel):
    """A Post created by user."""

    id: UUID = Field(
        default_factory=uuid4,
        description='The ID of the post.'
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description='Datetime of when the post was created.'
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description='Datetime of when the post was last updated.'
    )

    deleted_at: Optional[datetime] = Field(
        description='Datetime of when the post was soft deleted.')

    title: Optional[str] = Field(
        description='The title of the voice post.', max_length=40)

    location: Optional[str] = Field(
        max_length=50, description="Location of the video")

    video_uri: HttpUrl = Field(description='URI for the video recording.')

    post_type: PostType = Field(
        default=PostType.PUBLIC,
        description="Type of post public or private ."
    )

    from_user_id: UUID = Field(
        description='The ID of the user who uploaded the post.')
