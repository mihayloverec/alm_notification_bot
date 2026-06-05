from __future__ import annotations

import aiosqlite

from .users import User, _row_to_user


class OrganizersRepo:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def add(self, user_id: int) -> None:
        await self._conn.execute(
            "INSERT OR IGNORE INTO organizers (user_id) VALUES (?)",
            (user_id,),
        )
        await self._conn.commit()

    async def remove(self, user_id: int) -> None:
        await self._conn.execute(
            "DELETE FROM organizers WHERE user_id = ?",
            (user_id,),
        )
        await self._conn.commit()

    async def is_organizer(self, user_id: int) -> bool:
        async with self._conn.execute(
            "SELECT 1 FROM organizers WHERE user_id = ?",
            (user_id,),
        ) as cur:
            return await cur.fetchone() is not None

    async def list_users(self) -> list[User]:
        async with self._conn.execute(
            """
            SELECT u.user_id, u.username, u.first_name, u.is_blocked, u.is_banned, u.created_at
            FROM organizers o
            JOIN users u ON u.user_id = o.user_id
            ORDER BY o.added_at ASC
            """
        ) as cur:
            rows = await cur.fetchall()
        return [_row_to_user(r) for r in rows]
