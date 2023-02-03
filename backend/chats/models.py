import sqlalchemy as sa
from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError
from db import Base, metadata
from settings import LIMIT
from sqlalchemy.sql import func
from users.models import user

ProjectType = list[Record] | list[None]

room = sa.Table(
    "rooms", metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String(255), nullable=False, unique=True, index=True),
    sa.Column("timestamp", sa.DateTime(timezone=True), default=func.now()),
    sa.Column("is_active", sa.Boolean, default=False),
)
member = sa.Table(
    "members", metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete='CASCADE')),
    sa.Column("room_id", sa.Integer, sa.ForeignKey("rooms.id", ondelete='CASCADE')),
    sa.Column("create", sa.DateTime(timezone=True), default=func.now()),
    sa.UniqueConstraint('user_id', 'room_id', name='unique_member'),
)
message = sa.Table(
    "messages", metadata,
    sa.Column("key", sa.String, primary_key=True, unique=True, index=True),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete='CASCADE')),
    sa.Column("room_id", sa.Integer, sa.ForeignKey("rooms.id", ondelete='CASCADE')),
    sa.Column("content", sa.Text, nullable=False),
    sa.Column("create", sa.DateTime(timezone=True), default=func.now()),
)


class Room(Base):
    async def create(self, name: str, user_id: int) -> Record | None:
        return await self.database.fetch_one(
            sa.insert(room).values(name=name).returning(room)
        )

    async def by_name(self, name: str) -> Record | None:
        return await self.database.fetch_one(
            sa.select(room, func.count(member.c.user_id).label("is_count"))
            .join(member, member.c.room_id == room.c.id)
            .where(room.c.name == name)
            .group_by(room.c.id)
        )

    async def all_rooms(
        self,
        page: int = 1,
        limit: int = LIMIT,
        is_active: bool = False,
    ) -> ProjectType:

        query = (
            sa.select(room, func.count(member.c.user_id).label("is_count"))
            .join(member, member.c.room_id == room.c.id)
            .limit(limit)
            .offset((page - 1) * limit)
            .group_by(room.c.id)
            .order_by(room.c.timestamp.desc())
        )
        if is_active:
            query.where(room.c.is_active == is_active)
        return await self.database.fetch_all(query)

    async def update_is_active(self, room_id: int, bool_value: bool) -> Record | None:
        return await self.database.fetch_one(
            sa.update(room)
            .where(room.c.id == room_id)
            .values(is_active=bool_value)
            .returning(room)
        )

    async def delete(self, name: str) -> bool:
        await self.database.execute(
            sa.delete(room).where(room.c.name == name)
        )
        return True


class Member(Base):
    async def create(self, room_id: int, user_id: int) -> int | None:
        try:
            await self.database.execute(
                sa.insert(member).values(user_id=user_id, room_id=room_id)
            )
            return True
        except UniqueViolationError:
            return False

    async def user_in_room(self, room_name: str, user_id: int) -> Record | None:
        return await self.database.fetch_one(
            sa.select(room.c.id)
            .join(room, room.c.id == member.c.room_id)
            .where(room.c.name == room_name, member.c.user_id == user_id)
        )

    async def by_room_id(self, room_id: int, page: int = 1, limit: int = LIMIT) -> ProjectType:
        return await self.database.fetch_all(
            sa.select(
                user.c.id,
                user.c.username,
                user.c.firstname,
                user.c.lastname,
                user.c.image,
                user.c.timestamp,
                user.c.is_active,
            )
            .where(member.c.room_id == room_id)
            .join(user, user.c.id == member.c.user_id)
            .limit(limit)
            .offset((page - 1) * limit)
            .order_by(member.c.create.desc())
        )

    async def remove(self, room_id: int, user_id: int) -> bool:
        await self.database.execute(
            sa.delete(member).where(
                member.c.room_id == room_id,
                member.c.user_id == user_id,
            )
        )
        return True


class Message(Base):
    async def create(self, key: str, room_id: int, user_id: int, content: str) -> int | None:
        try:
            return await self.database.execute(
                sa.insert(message)
                .values(
                    key=key,
                    user_id=user_id,
                    room_id=room_id,
                    content=content
                )
            )
        except UniqueViolationError:
            return False

    async def get_all(self, room_id: int, page: int = 1, limit: int = LIMIT) -> ProjectType:
        return await self.database.fetch_all(
            sa.select(message.c.id, message.c.content, message.c.create)
            .where(message.c.room_id == room_id)
            .limit(limit)
            .offset((page - 1) * limit)
            .order_by(message.c.create.desc())
        )
