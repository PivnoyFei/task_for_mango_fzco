import uuid
from typing import Any

from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError
from chats import utils
from chats.models import Member, Message, Room
from chats.schemas import Friend, RoomName, RoomOut, UserWeb
from db import database
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from settings import LIMIT, LIMIT_MAX, NOT_FOUND
from starlette.websockets import WebSocket, WebSocketDisconnect
from users.models import User
from users.utils import get_current_user

router = APIRouter(prefix='/chat', tags=["chat"])
db_room = Room(database)
db_user = User(database)
db_member = Member(database)
db_message = Message(database)
manager = utils.ConnectionManager()
PROTECTED = Depends(get_current_user)


@router.post("/room", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create(room_name: RoomName, user: UserWeb = PROTECTED) -> Any:
    try:
        room = await db_room.create(room_name.name, room_name.privat)
        if room:
            await db_member.create(room.id, user.id)
            return room
    except UniqueViolationError:
        return JSONResponse(
            {"detail": "This room already exists."},
            status.HTTP_403_FORBIDDEN,
        )


@router.get("/room/{name}", response_model=RoomOut, status_code=status.HTTP_200_OK)
async def get_room(name: str, user: UserWeb = PROTECTED) -> JSONResponse:
    return await db_room.by_name(name) or NOT_FOUND


@router.get("/room/{name}/member", response_model=list[UserWeb], status_code=status.HTTP_200_OK)
async def get_members(
    name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(LIMIT, ge=LIMIT, lt=LIMIT_MAX),
    user: UserWeb = PROTECTED
) -> list[Record] | list[None] | JSONResponse:
    """Выдает список участников комнаты, доступна только для участников комнаты."""
    room = await db_member.user_in_room(name, user.id)
    if room:
        return await db_member.by_room_id(room.id, page, limit)
    return JSONResponse(
        {"detail": "Need to join a group"},
        status.HTTP_403_FORBIDDEN,
    )


@router.post("/room/{name}", status_code=status.HTTP_201_CREATED)
async def add_user_in_chat(name: str, friend: Friend, user: UserWeb = PROTECTED) -> JSONResponse:
    """Доступно только для участников чата."""
    room = await db_member.user_in_room(name, user.id)
    if room:
        _friend = await db_user.is_username(friend.username)
        if _friend:
            if await db_member.create(room.id, _friend.id):
                return JSONResponse({"detail": "OK"}, status.HTTP_201_CREATED)
    return JSONResponse(
        {"detail": "This user has already been added."},
        status.HTTP_403_FORBIDDEN,
    )


@router.get("/rooms", response_model=list[RoomOut], status_code=status.HTTP_200_OK)
async def get_all_rooms(
    page: int = Query(1, ge=1),
    limit: int = Query(LIMIT, ge=LIMIT, lt=LIMIT_MAX),
    is_active: bool = Query(True),
    user: UserWeb = PROTECTED,
) -> list[Record] | list[None]:
    """Выдает список активных или вообще всех комнат, доступна пагинация."""
    return await db_room.all_rooms(page, limit, is_active)


@router.delete("/room/{name}", status_code=status.HTTP_200_OK)
async def delete_room(name: str, user: UserWeb = PROTECTED) -> JSONResponse:
    if not await db_room.delete(name):
        return NOT_FOUND
    return JSONResponse({"detail": "OK"}, status.HTTP_200_OK)


@router.websocket("/ws/{room_name}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_name: str,
    limit: int = Query(LIMIT, ge=LIMIT, lt=LIMIT_MAX),
    user: UserWeb = Depends(utils.get_current_user)
) -> None:
    """
    Структура сообщений между пользователем и сервером: {
        "type": "Отключает соединение - disconnect или удаляет пользователя из группы - delete",
        "page": "Выдает список сообщений "messages". Лимит задается при подключении в limit.",
        "key": "uuid сообщения.",
        "content": "Текст сообщения.",
    }
    """
    room = await db_room.by_name(room_name, privat=True)
    if room and room.privat is True:
        if not await db_member.user_in_room(room_name, user.id):
            return

    if user and room:
        try:
            await manager.connect(websocket, room.id)
            if await db_member.create(room.id, user.id):
                """
                Добавляет пользователя в список участников группы.
                Если пользователь новый, уведомляет всех.
                """
                message = {
                    "room_id": room.id,
                    "user_id": user.id,
                    "content": f"{user.username} has entered the chat",
                }
                await manager.broadcast(message, room.id)

            while True:
                message = await websocket.receive_json()

                if "type" in message and message["type"] in ["disconnect", "delete"]:
                    await manager.disconnect(websocket, room.id)
                    if message["type"] == "delete":
                        await db_member.remove(room.id, user.id)
                        message = {
                            "room_id": room.id,
                            "user_id": user.id,
                            "content": f"{user.username} has left the chat",
                        }
                        await manager.broadcast(message, room.id)
                    break

                if "page" in message and int(message["page"]) > 0:
                    message_list = await db_message.get_all(room.id, int(message["page"]), limit)
                    all_messages = {
                        "room_id": room.id,
                        "user_id": user.id,
                        "messages": [dict(i) for i in message_list if i]
                    }
                    await manager.send_personal_message(all_messages, websocket)
                    continue
                """
                Сообщение из фронтенда приходит с uuid ключем
                по которому оно сохраняется и находиться в базе.
                """
                if "key" not in message or not await utils.is_valid_uuid(message["key"]):
                    message["key"] = uuid.uuid4().hex

                """Сохраняет и отправляет уведомление о получении сообщения для всех в группе."""
                if "content" in message:
                    if type(message["content"]) != str:
                        message["content"] = str(message["content"])
                    await db_message.create(message["key"], room.id, user.id, message["content"])
                    await manager.broadcast(
                        {
                            "accepted": True,
                            "key": message["key"],
                            "room_id": room.id,
                            "user_id": user.id,
                            "content": message["content"],
                        },
                        room.id,
                    )

        except WebSocketDisconnect:
            await manager.disconnect(websocket, room.id)
