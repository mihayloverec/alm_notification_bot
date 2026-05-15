from __future__ import annotations

from dataclasses import dataclass

import aiosqlite


@dataclass(frozen=True)
class User:
    user_id: int
    username: str | None
    first_name: str | None
    is_blocked: bool


class UsersRepo:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def upsert(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, is_blocked)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                is_blocked = 0
            """,
            (user_id, username, first_name),
        )
        await self._conn.commit()

    async def mark_blocked(self, user_id: int) -> None:
        await self._conn.execute(
            "UPDATE users SET is_blocked = 1 WHERE user_id = ?",
            (user_id,),
        )
        await self._conn.commit()

    async def get(self, user_id: int) -> User | None:
        async with self._conn.execute(
            "SELECT user_id, username, first_name, is_blocked FROM users WHERE user_id = ?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
        return _row_to_user(row) if row else None

    async def all_active_ids(self) -> list[int]:
        async with self._conn.execute(
            "SELECT user_id FROM users WHERE is_blocked = 0 ORDER BY user_id"
        ) as cur:
            rows = await cur.fetchall()
        return [r["user_id"] for r in rows]

    async def subscribed_active_ids(self, tournament_id: int) -> list[int]:
        async with self._conn.execute(
            """
            SELECT u.user_id
            FROM users u
            JOIN subscriptions s ON s.user_id = u.user_id
            WHERE u.is_blocked = 0 AND s.tournament_id = ?
            ORDER BY u.user_id
            """,
            (tournament_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [r["user_id"] for r in rows]


def _row_to_user(row: aiosqlite.Row) -> User:
    return User(
        user_id=row["user_id"],
        username=row["username"],
        first_name=row["first_name"],
        is_blocked=bool(row["is_blocked"]),
    )
