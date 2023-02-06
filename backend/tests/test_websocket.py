from typing import Any

from fastapi import status
from tests.conftest import Cache


def test_post_create_room(client: Any, room: dict, room_privat: dict) -> None:
    response = client.post("/api/chat/room", json=room, headers=Cache.headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == room["name"]
    assert response.json()["privat"] == room["privat"]

    response = client.post("/api/chat/room", json=room_privat, headers=Cache.headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == room_privat["name"]
    assert response.json()["privat"] == room_privat["privat"]


def test_get_room_name(client: Any, room: dict) -> None:
    room_name = room["name"]
    response = client.get(f"/api/chat/room/{room_name}", headers=Cache.headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == room["name"]


def test_get_members(client: Any, room: dict) -> None:
    room_name = room["name"]
    response = client.get(f"/api/chat/room/{room_name}/member", headers=Cache.headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_post_add_user_in_chat(
    client: Any,
    room: dict,
    room_privat: dict,
    user_one: dict,
    user_other: dict
) -> None:

    for room_name in [room["name"], room_privat["name"]]:
        json = {"username": user_other["username"]}
        response = client.post(
            f"/api/chat/room/{room_name}", json=json, headers=Cache.headers_other
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"detail": "This user has already been added."}
        response = client.get(f"/api/chat/room/{room_name}/member", headers=Cache.headers)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

        response = client.post(f"/api/chat/room/{room_name}", json=json, headers=Cache.headers)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"detail": "OK"}
        response = client.get(f"/api/chat/room/{room_name}/member", headers=Cache.headers)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2


def test_get_all_rooms(client: Any, room: dict) -> None:
    response = client.get("/api/chat/rooms", headers=Cache.headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    response = client.get("/api/chat/rooms", params={"is_active": False}, headers=Cache.headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert room["name"] in response.json()[0]["name"]


def test_delete_room(client: Any, room_privat: dict) -> None:
    room_name = room_privat["name"]
    response = client.delete(f"/api/chat/room/{room_name}", headers=Cache.headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "OK"}

    response = client.get(f"/api/chat/room/{room_name}", headers=Cache.headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
