from datetime import datetime
from uuid import uuid4, UUID
from pydantic import Field, HttpUrl, BaseModel


class VideoRecording(BaseModel):
    """A voice recording."""

    id: UUID = Field(
        default_factory=uuid4,
        description='The ID of the video.'
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description='Datetime of when the video was created.'
    )

    uploaded_by_user_id: UUID = Field(description='The ID of user who uploaded the video.')

    video_uri: HttpUrl = Field(description='URI for the video')
