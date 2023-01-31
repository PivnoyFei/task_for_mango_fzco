from typing import Any

from db import database
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, RedirectResponse
from redis import Redis
from settings import JWT_REFRESH_SECRET_KEY, REDIS_URL
from starlette.requests import Request
from users import utils
from users.deps_auth import OAuth2PasswordRequestForm as OAuth2Form
from users.models import User
from users.schemas import TokenBase, TokenSchema, UserOut

router = APIRouter(prefix='/auth', tags=["auth"])
db_redis = Redis.from_url(REDIS_URL, decode_responses=True)
db_user = User(database)


@router.post("/login", response_model=TokenSchema, status_code=status.HTTP_200_OK)
async def login(request: Request, user: OAuth2Form = Depends()) -> Any:
    """
    Authorization by phone and password, issues a token.
    Stores ip address and refresh token in Redis (Max 10 for user).
    {username: [{ip: refresh_token}]}.
    """

    user_cls = await db_user.password_by_username(user.username)
    if not user_cls:
        return JSONResponse({"detail": "Incorrect username"}, status.HTTP_400_BAD_REQUEST)

    if not await utils.verify_password(user.password, user_cls.password):
        return JSONResponse({"detail": "Incorrect password"}, status.HTTP_400_BAD_REQUEST)

    if request.client is not None:
        return await utils.redis_count_token_and_save(user.username, request.client.host)


@router.post('/refresh', response_model=TokenSchema, status_code=status.HTTP_200_OK)
async def refresh_token(request: Request, token: TokenBase) -> Any:
    """
    Validates the user's IP address and refresh token against a database entry.
    If the ip or refresh token doesn't match, it redirects to the authorization page..
    """
    if request.client is not None:
        username = await utils.check_token(
            token.refresh_token, JWT_REFRESH_SECRET_KEY, request.client.host
        )
        if username:
            return await utils.redis_count_token_and_save(username, request.client.host)
        return RedirectResponse('/api/auth/login', status.HTTP_302_FOUND)


@router.post("/logout", status_code=status.HTTP_404_NOT_FOUND)
async def logout(user: UserOut = Depends(utils.get_current_user)) -> None:
    """ Removes all user tokens. """
    db_redis.delete(user.username)
