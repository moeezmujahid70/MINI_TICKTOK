from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4, UUID

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from starlette import status

from miniTicktok_api.config import config
from miniTicktok_api.external.mongodb import MongodbDatabase
from miniTicktok_api.models.users import User
from miniTicktok_api.services import services


class TokenData(BaseModel):
    username: Optional[str] = None


class AccessToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class RefreshToken(BaseModel):
    refresh_token: str
    access_token: str
    token_type: str = 'bearer'
    token_family: UUID = Field()
    used: bool = False
    invalidated: bool = False


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/oauth/token")


async def _get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user_data = services.get(MongodbDatabase).database.get_collection(
        'users').find_one({"id": UUID(token_data.username)})

    if user_data is None:
        raise credentials_exception

    user = User.parse_obj(user_data)

    return user


async def get_current_user(user: User = Depends(_get_current_user)) -> User:
    if user.deleted_at:
        raise HTTPException(status_code=400, detail="Inactive user.")

    return user


def _create_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.jwt_secret, algorithm=config.jwt_algorithm)

    return encoded_jwt


def generate_access_token(user: User) -> AccessToken:
    token_family = uuid4()

    refresh_token_string = _create_token(
        data={"sub": str(token_family)},
        expires_delta=timedelta(days=config.jwt_refresh_token_expire_days),
    )

    access_token_string = _create_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=config.jwt_access_token_expire_minutes),
    )

    refresh_token = RefreshToken(
        refresh_token=refresh_token_string,
        access_token=access_token_string,
        token_family=token_family
    )
    refresh_tokens_collection = services.get(MongodbDatabase).database.get_collection('refresh_tokens')
    refresh_tokens_collection.insert_one(refresh_token.dict())

    return AccessToken(access_token=access_token_string, refresh_token=refresh_token_string)


def new_access_token_from_refresh_token(old_refresh_token):
    new_token = _create_token(
        data={"sub": str(old_refresh_token.token_family)},
        expires_delta=timedelta(days=config.jwt_refresh_token_expire_days),
    )

    decoded_access_token = jwt.decode(
        old_refresh_token.access_token,
        config.jwt_secret,
        algorithms=[config.jwt_algorithm],
        options={'verify_exp': False},
    )

    access_token_string = _create_token(
        data={"sub": decoded_access_token["sub"]},
        expires_delta=timedelta(minutes=config.jwt_access_token_expire_minutes),
    )

    new_refresh_token = RefreshToken(
        refresh_token=new_token,
        access_token=access_token_string,
        token_family=old_refresh_token.token_family,
    )
    refresh_tokens_collection = services.get(MongodbDatabase).database.get_collection('refresh_tokens')
    refresh_tokens_collection.insert_one(new_refresh_token.dict())

    return AccessToken(access_token=access_token_string, refresh_token=new_refresh_token.refresh_token)
