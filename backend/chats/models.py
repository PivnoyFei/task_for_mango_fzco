import sqlalchemy as sa
from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError
from db import Base, metadata
from sqlalchemy.sql import func

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
    sa.UniqueConstraint('user_id', 'room_id', name='unique_member'),
)
message = sa.Table(
    "messages", metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete='CASCADE')),
    sa.Column("room_id", sa.Integer, sa.ForeignKey("rooms.id", ondelete='CASCADE')),
    sa.Column("content", sa.Text, nullable=False),
    sa.Column("create", sa.DateTime(timezone=True), default=func.now()),
    sa.UniqueConstraint('user_id', 'room_id', name='unique_message')
)


class Room(Base):
    async def create(self, name: str) -> Record | None:
        return await self.database.fetch_one(
            sa.insert(room).values(name=name).returning(room)
        )

    async def by_name(self, name: str) -> Record | None:
        return await self.database.fetch_one(
            sa.select(room).where(room.c.name == name)
        )

    async def all_rooms(
        self,
        page: int = 1,
        limit: int = 6,
        is_active: bool = False
    ) -> list[Record] | list[None]:

        query = (
            sa.select(room)
            .limit(limit)
            .offset((page - 1) * limit)
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
            return await self.database.execute(
                sa.insert(member).values(user_id=user_id, room_id=room_id)
            )
        except UniqueViolationError:
            return False

    async def remove(self, room_id: int, user_id: int) -> bool:
        await self.database.execute(
            sa.delete(member).where(
                member.c.room_id == room_id,
                member.c.user_id == user_id,
            )
        )
        return True
