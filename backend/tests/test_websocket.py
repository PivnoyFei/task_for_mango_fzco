from typing import Any

from fastapi import status
from tests.conftest import Cache


def test_post_create_room(client: Any, user_one: dict, room: dict) -> None:
    response = client.post("/api/chat/room", json=room, headers=Cache.headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {'detail': 'OK'}


def test_websocket(client: Any, user_one: dict, room: str) -> None:
    username = user_one["username"]
    room_name = room["name"]
    with client.websocket_connect(f"/api/chat/ws/{room_name}/{username}") as websocket:
        data = websocket.receive_json()
        assert data["user"] == username
        assert data["room_name"] == room_name
