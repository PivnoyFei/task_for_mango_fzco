import json

from chats.models import Room
from db import database
from starlette.websockets import WebSocket

db_room = Room(database)


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

    async def broadcast(self, message: dict) -> None:
        for connection in self.active_connections:
            await connection.send_text(f"{json.dumps(message, default=str)}")
