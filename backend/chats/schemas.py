from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserWeb(BaseModel):
    id: int
    firstname: str
    lastname: str
    image: str | None = ""
    username: str
    timestamp: datetime


class MessageWeb(BaseModel):
    user: UserWeb
    content: str


class RoomName(BaseModel):
    name: str


class RoomWeb(RoomName):
    members: Optional[list[UserWeb]] = []
    messages: Optional[list[MessageWeb]] = []
    active: bool = False
