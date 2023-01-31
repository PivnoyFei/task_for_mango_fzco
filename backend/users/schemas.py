import datetime
import re
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, root_validator, validator


class UserUpdate(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    image: str | None = None


class UserBase(BaseModel):
    firstname: str
    lastname: str
    image: str | None = None
    username: str = Field(..., min_length=5, max_length=25)
    phone: str
    email: EmailStr


class UserOut(UserBase):
    id: int
    timestamp: datetime.datetime


class UserCreate(UserBase):
    password: str

    @validator("username", "firstname", "lastname",)
    def validator(cls, value: str) -> str:
        if not value.isalpha():
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Unacceptable symbols"
            )
        return value

    @root_validator()
    def validate_mobile(cls, value: Any) -> Any:
        rule = re.compile(r'^[0-9]{10,14}$')

        if not rule.search(value["phone"]):
            raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid mobile number."
            )
        return value


class UserAuth(BaseModel):
    phone: str = Field(...,)
    password: str = Field(...,)


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    exp: int


class TokenBase(BaseModel):
    refresh_token: str = Field(...,)
