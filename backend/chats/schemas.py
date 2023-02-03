from datetime import datetime

from pydantic import BaseModel


class UserWeb(BaseModel):
    id: int
    firstname: str
    lastname: str
    image: str | None = ""
    username: str
    timestamp: datetime
    is_active: bool


class MessageWeb(BaseModel):
    user: UserWeb
    content: str


class RoomName(BaseModel):
    name: str


class RoomOut(RoomName):
    id: int
    timestamp: datetime
    is_active: bool | None = False
    is_count: int | None = 0
