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


class Friend(BaseModel):
    username: str


class RoomName(BaseModel):
    name: str
    privat: bool


class RoomOut(RoomName):
    id: int
    timestamp: datetime
    privat: bool
    is_active: bool = False
    is_count: int | None = 0
