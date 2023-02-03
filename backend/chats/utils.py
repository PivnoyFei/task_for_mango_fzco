import json
from typing import Any, Optional

from chats.models import Room
from db import database
from fastapi import Depends, WebSocket
from settings import JWT_ACCESS_SECRET_KEY
from users.deps_auth import WebSocketOAuth2PasswordBearer
from users.utils import check_token

db_room = Room(database)
ws_oauth2_scheme = WebSocketOAuth2PasswordBearer(token_url='/chat/token')


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket, room_id: int) -> None:
        await websocket.accept()
        await db_room.update_is_active(room_id, True)
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket, room_id: int = 0) -> None:
        self.active_connections.remove(websocket)
        if len(self.active_connections) == 0:
            await db_room.update_is_active(room_id, False)

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        await websocket.send_text(f"{json.dumps(message, default=str)}")

    async def broadcast(self, message: dict) -> None:
        for connection in self.active_connections:
            await connection.send_text(f"{json.dumps(message, default=str)}")


async def get_current_user(token: Optional[str] = Depends(ws_oauth2_scheme)) -> Any:
    """Проверка токена для вебсокета."""
    if token is None:
        return None
    return await check_token(token, JWT_ACCESS_SECRET_KEY)
