from typing import Any

from db import database
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from settings import NOT_FOUND
from starlette.requests import Request
from users import utils
from users.models import User
from users.schemas import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix='/users', tags=["users"])
db_user = User(database)
PROTECTED = Depends(utils.get_current_user)


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(request: Request, user: UserCreate) -> Any:

    if await db_user.is_email(user.email):
        return JSONResponse({"message": "Email already exists"}, status.HTTP_400_BAD_REQUEST)

    if await db_user.is_username(user.username):
        return JSONResponse({"message": "Username already exists"}, status.HTTP_400_BAD_REQUEST)

    if await db_user.is_phone(user.phone):
        return JSONResponse({"message": "Phone already exists"}, status.HTTP_400_BAD_REQUEST)

    user.password = await utils.get_hashed_password(user.password)
    if user.image:
        user.image = await utils.base64_image(user.image)
    try:
        newuser = await db_user.create(user)
    except Exception:
        if user.image:
            await utils.image_delete(user.image)
        return JSONResponse({"detail": "Error users"}, status.HTTP_400_BAD_REQUEST)
    return await utils.path_image(request, newuser)


@router.get('/me', response_model=UserOut, status_code=status.HTTP_200_OK)
async def me(request: Request, user: UserOut = PROTECTED) -> Any:
    """ Get details of currently logged in user. """
    return await utils.path_image(request, user)


@router.get("/{username}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def user_id(request: Request, username: str) -> dict | JSONResponse:
    """ User profile. Available to all users. """
    return await utils.path_image(request, await db_user.by_username(username)) or NOT_FOUND


@router.put("/{username}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_user(
    request: Request,
    user_obj: UserUpdate,
    username: str,
    user: UserOut = PROTECTED
) -> Any:
    """ Update_user {firstname, lastname, image}. """
    if username == user.username:
        if user_obj.image:
            user_obj.image = await utils.base64_image(user_obj.image)
        user_dict = {
            "firstname": user_obj.firstname if user_obj.firstname else user.firstname,
            "lastname": user_obj.lastname if user_obj.lastname else user.lastname,
            "image": user_obj.image if user_obj.image else user.image,
        }
        try:
            result = await db_user.update(username, user_dict)
            if user_obj.image:
                await utils.image_delete(user.image)
            return await utils.path_image(request, result)

        except Exception:
            if user_obj.image:
                await utils.image_delete(user_obj.image)
            return JSONResponse({"detail": "Error users"}, status.HTTP_400_BAD_REQUEST)

    return JSONResponse({"detail": "Forbidden"}, status.HTTP_403_FORBIDDEN)
