from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError
from chats import utils
from chats.models import Member, Room
from chats.schemas import RoomName
from db import database
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from settings import NOT_FOUND
from starlette.websockets import WebSocket, WebSocketDisconnect
from users.models import User
from users.utils import get_current_user

router = APIRouter(prefix='/chat', tags=["chat"])
db_room = Room(database)
db_user = User(database)
db_member = Member(database)
manager = utils.ConnectionManager()
PROTECTED = Depends(get_current_user)


@router.post("/room", status_code=status.HTTP_201_CREATED)
async def create_room(room_name: RoomName, user: Record = PROTECTED) -> JSONResponse:
    try:
        await db_room.create(room_name.name)
        return JSONResponse({"detail": "OK"}, status.HTTP_201_CREATED)
    except UniqueViolationError:
        return JSONResponse(
            {"detail": "This room already exists."},
            status.HTTP_403_FORBIDDEN,
        )


@router.get("/room/{name}", response_model=RoomName, status_code=status.HTTP_200_OK)
async def get_room(name: str, user: Record = PROTECTED) -> JSONResponse:
    return await db_room.by_name(name) or NOT_FOUND


@router.get("/rooms", response_model=list[RoomName], status_code=status.HTTP_200_OK)
async def get_all_rooms(
    page: int = Query(1, ge=1),
    limit: int = Query(6, ge=1),
    is_active: bool = Query(False),
    user: Record = PROTECTED,
) -> list[Record] | list[None]:
    return await db_room.all_rooms(page, limit, is_active)


@router.delete("/room/{name}", status_code=status.HTTP_200_OK)
async def delete_room(name: str, user: Record = PROTECTED) -> JSONResponse:
    if not await db_room.delete(name):
        return NOT_FOUND
    return JSONResponse({"detail": "OK"}, status.HTTP_200_OK)


@router.websocket("/ws/{room_name}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, username: str) -> None:
    room = await db_room.by_name(room_name)
    user = await db_user.by_username(username)
    if user and room:
        try:
            await manager.connect(websocket, room.id)
            if await db_member.create(room.id, user.id):
                message = {
                    "content": f"{username} has entered the chat",
                    "user": username,
                    "room_name": room_name,
                }
                await manager.broadcast(message)
            while True:
                message = await websocket.receive_json()
                if "type" in message and message["type"] == "disconnect":
                    await manager.disconnect(websocket, room.id)
                    break
                await manager.broadcast({"accepted": True})
        except WebSocketDisconnect:
            await db_member.remove(room.id, user.id)
            message = {
                "content": f"{username} has left the chat",
                "user": username,
                "room_id": room_name,
            }
            await manager.broadcast(message)
            await manager.disconnect(websocket, room.id)
