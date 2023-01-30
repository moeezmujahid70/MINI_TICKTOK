import random
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, EmailStr


def _random_discriminator():
    return random.randint(1000, 9999)


class User(BaseModel):
    """A user where all data is available."""

    id: UUID = Field(
        default_factory=uuid4,
        description='The ID of the user.'
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description='Datetime of when the user was created.'
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description='Datetime of when the user was last updated.'
    )

    deleted_at: Optional[datetime] = Field(description='Datetime of when the user was soft deleted.')

    email: Optional[EmailStr] = Field(description='The e-mail of the user.')

    username: str = Field(
        description='The username of the user.',
        max_length=30,
        min_length=3,
    )

    username_discriminator: int = Field(
        description='A discriminator that makes sure no users have the same tag.',
        default_factory=_random_discriminator,
        ge=1000,
        le=9999,
    )

    tag: Optional[str] = Field(description='A unique tag belonging to the user.')

    password: Optional[str] = Field(description="The hashed version of the user's password.")

    @classmethod
    def create_tag(cls, username: str, username_discriminator: Optional[int] = None) -> str:
        if not username_discriminator:
            username_discriminator = _random_discriminator()

        return f'{username}#{username_discriminator}'


class PublicUser(BaseModel):
    """A user where only public data is available."""

    id: UUID = Field(
        default_factory=uuid4,
        description='The ID of the user.'
    )

    username: str = Field(description='The username of the user.')
    tag: Optional[str] = Field(description='A unique tag belonging to the user.')
