import sqlalchemy as sa
from asyncpg import Record
from db import Base, metadata
from sqlalchemy.sql import func
from users.schemas import UserCreate

user = sa.Table(
    "users", metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("email", sa.String(255), nullable=False, unique=True),
    sa.Column("phone", sa.String(14), nullable=False, unique=True),
    sa.Column("password", sa.String(255), nullable=False),
    sa.Column("username", sa.String(150), nullable=False, unique=True, index=True),
    sa.Column("firstname", sa.String(150), nullable=False),
    sa.Column("lastname", sa.String(150), nullable=False),
    sa.Column("image", sa.String(200), unique=True),
    sa.Column("timestamp", sa.DateTime(timezone=True), default=func.now()),
    sa.Column("is_active", sa.Boolean, default=True)
)


class User(Base):
    async def user_by_username(self, username: str) -> Record:
        return await self.database.fetch_one(
            sa.select(user).where(user.c.username == username)
        )

    async def is_email(self, email: str) -> Record | None:
        return await self.database.fetch_one(
            sa.select(user.c.id).where(user.c.email == email)
        )

    async def is_username(self, username: str) -> Record | None:
        return await self.database.fetch_one(
            sa.select(user.c.username).where(user.c.username == username)
        )

    async def is_phone(self, phone: str) -> Record | None:
        return await self.database.fetch_one(
            sa.select(user.c.phone).where(user.c.phone == phone)
        )

    async def password_by_username(self, username: str) -> Record | None:
        return await self.database.fetch_one(
            sa.select(user.c.password).where(user.c.username == username)
        )

    async def create(self, user_obj: UserCreate) -> Record:
        return await self.database.fetch_one(
            sa.insert(user).values(
                username=user_obj.username,
                firstname=user_obj.firstname,
                lastname=user_obj.lastname,
                phone=user_obj.phone,
                email=user_obj.email,
                password=user_obj.password,
                is_active=True,
            ).returning(user)
        )

    async def update(self, username: str, user_obj: dict) -> Record | None:
        return await self.database.fetch_one(
            sa.update(user)
            .where(user.c.username == username)
            .values(user_obj)
            .returning(user)
        )
