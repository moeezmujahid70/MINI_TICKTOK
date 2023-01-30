from typing import List
from uuid import uuid4
from mega import Mega
import os

from fastapi import APIRouter, Depends, File, Form, UploadFile

from miniTicktok_api.auth import get_current_user
from miniTicktok_api.external.mongodb import MongodbDatabase
from miniTicktok_api.models.users import User
from miniTicktok_api.models.videos import VideoRecording
from miniTicktok_api.services import services

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =================== Router ==================== #


router = APIRouter(
    prefix='/video_recordings',
    tags=['Video Recordings'],
    dependencies=[Depends(get_current_user)],
)


# =============== Response Models =============== #


class CreateVideoRequest:
    def __init__(
            self,
            file: UploadFile = File(...),
    ):
        self.file = file


# ================== Endpoints ================== #

@router.post(
    path='',
    description='Upload and create video recording that can be attached to feed posts.',

)
async def create_voice(
        request: CreateVideoRequest = Depends(CreateVideoRequest),
        user: User = Depends(get_current_user),
):
    voice_recordings_collection = services.get(MongodbDatabase).database.get_collection('video_recordings')

    voice_id = uuid4()
    file_name = f'video-rec-{str(voice_id)}.mp4'

    file_path = f"./{request.file.filename}"

    mega = Mega()
    m = mega.login(os.getenv("APP_MEGA_EMAIL"), os.getenv("APP_MEGA_PASSWORD"))

    with open(file_path, "wb") as f:
        f.write(await request.file.read())

    m.upload(file_path, dest_filename=file_name)

    file = m.find(file_name)
    video_uri = m.get_link(file)

    voice_recording = VideoRecording(
        id=voice_id,
        uploaded_by_user_id=user.id,
        video_uri=video_uri,
    )

    if os.path.exists(file_path):
        os.remove(file_path)

    voice_recordings_collection.insert_one(voice_recording.dict())
    return video_uri
