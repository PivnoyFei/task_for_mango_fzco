import uuid

from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError
from chats import utils
from chats.models import Member, Message, Room
from chats.schemas import RoomName, RoomOut, UserWeb
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


@router.post("/room", status_code=status.HTTP_201_CREATED)
async def create_room(room_name: RoomName, user: Record = PROTECTED) -> JSONResponse:
    try:
        await db_room.create(room_name.name, user.id)
        return JSONResponse({"detail": "OK"}, status.HTTP_201_CREATED)
    except UniqueViolationError:
        return JSONResponse(
            {"detail": "This room already exists."},
            status.HTTP_403_FORBIDDEN,
        )


@router.get("/room/{name}", response_model=RoomOut, status_code=status.HTTP_200_OK)
async def get_room(name: str, user: Record = PROTECTED) -> JSONResponse:
    return await db_room.by_name(name) or NOT_FOUND


@router.get("/room/{name}/member", response_model=list[UserWeb], status_code=status.HTTP_200_OK)
async def get_members(
    name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(LIMIT, ge=LIMIT, lt=LIMIT_MAX),
    user: Record = PROTECTED
) -> list[Record] | list[None] | JSONResponse:
    """Выдает список участников комнаты, доступна только для участников комнаты."""
    room = await db_member.user_in_room(name, user.id)
    if room:
        return await db_member.by_room_id(room.id, page, limit)
    return JSONResponse(
        {"detail": "Need to join a group"},
        status.HTTP_403_FORBIDDEN,
    )


@router.get("/rooms", response_model=list[RoomOut], status_code=status.HTTP_200_OK)
async def get_all_rooms(
    page: int = Query(1, ge=1),
    limit: int = Query(LIMIT, ge=LIMIT, lt=LIMIT_MAX),
    is_active: bool = Query(False),
    user: Record = PROTECTED,
) -> list[Record] | list[None]:
    """Выдает список активных или вообще всех комнат, доступна пагинация."""
    return await db_room.all_rooms(page, limit, is_active)


@router.delete("/room/{name}", status_code=status.HTTP_200_OK)
async def delete_room(name: str, user: Record = PROTECTED) -> JSONResponse:
    if not await db_room.delete(name):
        return NOT_FOUND
    return JSONResponse({"detail": "OK"}, status.HTTP_200_OK)


@router.websocket("/ws/{room_name}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(LIMIT, ge=LIMIT, lt=LIMIT_MAX),
    user: UserWeb = Depends(utils.get_current_user)
) -> None:

    room = await db_room.by_name(room_name)
    if user and room:
        try:
            await manager.connect(websocket, room.id)
            """
            Добавляет пользователя в список участников чата.
            Если пользователь новый, уведомляет всех.
            """
            if await db_member.create(room.id, user.id):
                message = {"content": f"{user.username} has entered the chat"}
                await manager.send_personal_message(message, websocket)

            while True:
                message = await websocket.receive_json()

                """Отключает соединение."""
                if "type" in message and message["type"] == "disconnect":
                    await manager.disconnect(websocket, room.id)
                    break

                """Выдает список сообщений. Пагинация настраиваеться при подклбчении."""
                if "messages" in message and message["messages"] == "get":
                    messages_list = await db_message.get_all(room.id, page, limit)
                    all_messages = {
                        "room_id": room.id,
                        "user_id": user.id,
                        "all_messages": messages_list
                    }
                    await manager.send_personal_message(all_messages, websocket)

                """
                Сообщение из фронтенда приходит с uuid ключем 
                по которому оно сохраняется и находиться в базе.
                """
                if "key" not in message or message["key"] == "":
                    message["key"] = str(uuid.uuid4().hex)

                """Текст сообщения. Сохраняет и отправляет уведосление о получении."""
                if "content" in message and message["content"]:
                    await db_message.create(
                        message["key"],
                        room.id,
                        user.id,
                        message["content"],
                    )
                    await manager.send_personal_message(
                        {
                            "accepted": True,
                            "key": message["key"]
                        },
                        websocket,
                    )

        except WebSocketDisconnect:
            await db_member.remove(room.id, user.id)
            message = {"content": f"{user.username} has left the chat"}
            await manager.send_personal_message(message, websocket)
            await manager.disconnect(websocket, room.id)
