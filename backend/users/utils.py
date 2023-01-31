import base64
import binascii
import os
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import aiofiles
import settings
from db import database
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.hash import bcrypt
from PIL import Image
from pydantic import ValidationError
from redis import Redis
from settings import (ALLOWED_TYPES, AVATAR_ROOT, INVALID_FILE, INVALID_TYPE,
                      REDIS_URL, SIZES)
from users.models import User
from users.schemas import TokenPayload

db_user = User(database)
db_redis = Redis.from_url(REDIS_URL, decode_responses=True)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    scheme_name="JWT"
)


async def get_hashed_password(password: str) -> str:
    """ Hashes the user's password. """
    return bcrypt.hash(password)


async def verify_password(password: str, hashed_pass: str) -> bool:
    """ Validates a hashed user password. """
    return bcrypt.verify(password, hashed_pass)


async def _get_token(sub: str, secret: str, expire_minutes: int) -> str:
    """ Called from create_access_token and create_refresh_token. """
    exp = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode = {"exp": exp, "sub": str(sub)}
    encoded_jwt = jwt.encode(to_encode, secret, settings.ALGORITHM)
    return encoded_jwt


async def create_access_token(sub: str) -> str:
    """ Creates a access token. """
    return await _get_token(
        sub,
        settings.JWT_ACCESS_SECRET_KEY,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


async def create_refresh_token(sub: str) -> str:
    """ Creates a refresh token. """
    return await _get_token(
        sub,
        settings.JWT_REFRESH_SECRET_KEY,
        settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )


async def check_token(token: str, secret: str, refresh_host: str = '') -> Any:
    """
    Checks the token time.
    if refresh_token checks if the IP address exists in the database.
    if not, removes all tokens
    """
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    try:
        payload = jwt.decode(
            token, secret, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise exception
        if refresh_host:
            if db_redis.hmget(token_data.sub, refresh_host)[0] == token:
                return token_data.sub
            db_redis.hdel(token_data.sub, refresh_host)
            raise exception

    except (JWTError, ValidationError):
        raise exception

    user = await db_user.user_by_username(token_data.sub)
    if not user:
        raise exception
    return user


async def redis_count_token_and_save(username: str, host: str) -> dict[str, str]:
    access_token = await create_access_token(username)
    refresh_token = await create_refresh_token(username)

    if len(db_redis.hgetall(username)) > 10:
        db_redis.delete(username)
    db_redis.hmset(username, {host: refresh_token})

    return {"access_token": access_token, "refresh_token": refresh_token}


async def get_current_user(token: str = Depends(oauth2_scheme)) -> type:
    """ Checks the currently logged in user. """
    return await check_token(token, settings.JWT_ACCESS_SECRET_KEY)


async def image_delete(filename: str) -> None:
    filename, extension = filename.split(".")

    for size in ["", *SIZES]:
        image_path = os.path.join(AVATAR_ROOT, f"{filename}{size}.{extension}")
        if os.path.isfile(image_path):
            os.remove(image_path)


async def base64_image(base64_data: str, extension: str = "jpg") -> str:
    """
    Checks the file format, if it exists.
    After successful base64 decoding, the file will be saved in 3 sizes:
    50x50, 100x100, 400x400, and original.
    """
    if ";base64," in base64_data:
        header, base64_data = base64_data.split(";base64,")
        name, extension = header.split("/")
        if extension.lower() not in ALLOWED_TYPES:
            raise HTTPException(status.HTTP_418_IM_A_TEAPOT, INVALID_TYPE)

    filename = f"{uuid4()}"
    image_path = os.path.join(AVATAR_ROOT, f"{filename}.{extension}")
    try:
        async with aiofiles.open(image_path, "wb") as buffer:
            await buffer.write(base64.b64decode(base64_data))

        for size in SIZES:
            image = Image.open(image_path, mode="r")
            image.thumbnail((size, size))
            image.save(os.path.join(AVATAR_ROOT, f"{filename}{size}.{extension}"))

    except (Exception, TypeError, binascii.Error, ValueError):
        raise HTTPException(status.HTTP_418_IM_A_TEAPOT, INVALID_FILE)
    return f"{filename}.{extension}"
