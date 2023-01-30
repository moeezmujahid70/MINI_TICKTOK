from typing import Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Form
from jose import jwt, ExpiredSignatureError
from starlette import status

from miniTicktok_api.auth import RefreshToken, AccessToken, generate_access_token, new_access_token_from_refresh_token
from miniTicktok_api.config import config
from miniTicktok_api.crpyto import verify_password
from miniTicktok_api.external.mongodb import MongodbDatabase
from miniTicktok_api.models.users import User
from miniTicktok_api.services import services

# =================== Router ==================== #


router = APIRouter(
    prefix='/oauth',
    tags=['Authentication'],
)


# =============== Response Models =================== #


class OAuth2RequestForm:
    def __init__(
            self,
            grant_type: str = Form(""),
            username: str = Form(""),
            password: str = Form(""),
            refresh_token: str = Form(""),
            scope: str = Form(""),
            client_id: Optional[str] = Form(None),
            client_secret: Optional[str] = Form(None),
    ):
        self.grant_type = grant_type
        self.username = username
        self.password = password
        self.refresh_token = refresh_token
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


# =============== Private Methods =================== #


def _authenticate_user(email: str, password: str) -> Union[bool, User]:
    user_data = services.get(MongodbDatabase).database.get_collection('users').find_one({"email": email})

    if not user_data:
        return False

    user = User.parse_obj(user_data)

    if not verify_password(password, user.password):
        return False

    return user


def _purge_refresh_tokens(token_family: UUID):
    refresh_tokens_collection = services.get(MongodbDatabase).database.get_collection('refresh_tokens')
    refresh_tokens_collection.update_many({"token_family": token_family}, {'$set': {'invalidated': True}})


def _refresh_token(refresh_token: str) -> AccessToken:
    refresh_tokens_collection = services.get(MongodbDatabase).database.get_collection('refresh_tokens')
    refresh_token_data = refresh_tokens_collection.find_one({"refresh_token": refresh_token})

    if not refresh_token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Old refresh token not found.",
        )

    old_refresh_token = RefreshToken.parse_obj(refresh_token_data)

    try:
        jwt.decode(old_refresh_token.refresh_token, config.jwt_secret, algorithms=[config.jwt_algorithm])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired.",
        )

    if old_refresh_token.used or old_refresh_token.invalidated:
        _purge_refresh_tokens(old_refresh_token.token_family)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token already used or invalidated.",
        )

    old_refresh_token.used = True
    refresh_tokens_collection.replace_one(
        {"refresh_token": old_refresh_token.refresh_token}, old_refresh_token.dict())

    return new_access_token_from_refresh_token(old_refresh_token)


def _access_token(form_data: OAuth2RequestForm):
    user = _authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return generate_access_token(user)


# ================== Endpoints ================== #


@router.post(
    "/token",
    response_model=Union[AccessToken, RefreshToken],
    description='Create an access token and a refresh token.',
)
async def oauth_token(form_data: OAuth2RequestForm = Depends()) -> AccessToken:
    if form_data.grant_type == 'refresh_token':
        if not form_data.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Missing "refresh_token" field.',
            )

        return _refresh_token(form_data.refresh_token)

    return _access_token(form_data)
