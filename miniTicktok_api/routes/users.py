from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, BaseModel
from starlette import status

from miniTicktok_api.auth import get_current_user
from miniTicktok_api.crpyto import get_password_hash
from miniTicktok_api.external.mongodb import MongodbDatabase
from miniTicktok_api.services import services
from miniTicktok_api.models.users import User
# =================== Router ==================== #


router = APIRouter(
    prefix='/users',
    tags=['Users and Registration'],
)

# ================== Endpoints ================== #


class CreateUserRequest(BaseModel):
    email: str = Field(description='The e-mail of the user.')
    username: str = Field(
        description='The username of the user.',
        max_length=30,
        min_length=3,
    )
    password: str = Field(description="The plain text version of the user's password.")
    password_verification: str = Field(description="The same password for verification purposes.")


# ================== Endpoints ================== #


@router.get(
    path='/me',
    description='Get details about the authenticated user.',
    response_model=User,
)
async def get_my_info(user: User = Depends(get_current_user)) -> User:
    return user


@router.post(
    path='',
    description='Create a user. Use this to register new users manually without social-logins.',
    response_model=User,
)
async def create_user(request: CreateUserRequest) -> User:
    # ================== CREATE USER ================== #

    if request.password != request.password_verification:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Passwords are not identical.")

    password = get_password_hash(request.password)

    users_collection = services.get(MongodbDatabase).database.get_collection('users')

    if users_collection.count_documents({'email': request.email, 'deleted_at': None}, limit=1) != 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail already registered.")

    has_unique_user_tag = False
    tries = 0
    user = None

    while not has_unique_user_tag and tries < 30:
        user = User(
            email=request.email,
            username=request.username,
            password=password,
        )

        user.tag = User.create_tag(username=user.username, username_discriminator=user.username_discriminator)

        if users_collection.count_documents({'tag': user.tag, 'deleted_at': None}, limit=1) == 0:
            has_unique_user_tag = True

        tries += 1

    if not user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Failed to create user.")

    users_collection.insert_one(user.dict())

    return user
