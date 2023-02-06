import json
import uuid
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
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int) -> None:
        """Создает словарь с ключом группы и значением в виде списка коннектов."""
        await websocket.accept()
        await db_room.update_is_active(room_id, True)
        if room_id in self.active_connections:
            self.active_connections[room_id].append(websocket)
        else:
            self.active_connections[room_id] = [websocket]

    async def disconnect(self, websocket: WebSocket, room_id: int = 0) -> None:
        """Удаляет коннект пользователя из группы."""
        self.active_connections[room_id].remove(websocket)
        if room_id in self.active_connections and len(self.active_connections[room_id]) == 0:
            await db_room.update_is_active(room_id, False)

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """Отправляет персональные сообщения."""
        await websocket.send_text(f"{json.dumps(message, ensure_ascii=False, default=str)}")

    async def broadcast(self, message: dict, room_id: int) -> None:
        """Отправляет сообщения всем в группе."""
        for connection in self.active_connections[room_id]:
            await connection.send_text(f"{json.dumps(message, ensure_ascii=False, default=str)}")


async def get_current_user(token: Optional[str] = Depends(ws_oauth2_scheme)) -> Any:
    """Проверка токена для вебсокета."""
    if token is None:
        return None
    return await check_token(token, JWT_ACCESS_SECRET_KEY)


async def is_valid_uuid(val: Any) -> bool:
    """Проверка ключа по которому сохраняется сообщение."""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False
