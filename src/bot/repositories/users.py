from __future__ import annotations

from dataclasses import dataclass

import aiosqlite


@dataclass(frozen=True)
class User:
    user_id: int
    username: str | None
    first_name: str | None
    is_blocked: bool
    is_banned: bool
    created_at: str


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

    async def set_banned(self, user_id: int, banned: bool) -> None:
        await self._conn.execute(
            "UPDATE users SET is_banned = ? WHERE user_id = ?",
            (1 if banned else 0, user_id),
        )
        await self._conn.commit()

    async def get(self, user_id: int) -> User | None:
        async with self._conn.execute(
            "SELECT user_id, username, first_name, is_blocked, is_banned, created_at "
            "FROM users WHERE user_id = ?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
        return _row_to_user(row) if row else None

    async def all_active_ids(self) -> list[int]:
        async with self._conn.execute(
            "SELECT user_id FROM users "
            "WHERE is_blocked = 0 AND is_banned = 0 ORDER BY user_id"
        ) as cur:
            rows = await cur.fetchall()
        return [r["user_id"] for r in rows]

    async def subscribed_active_ids(self, tournament_id: int) -> list[int]:
        async with self._conn.execute(
            """
            SELECT u.user_id
            FROM users u
            JOIN subscriptions s ON s.user_id = u.user_id
            WHERE u.is_blocked = 0 AND u.is_banned = 0 AND s.tournament_id = ?
            ORDER BY u.user_id
            """,
            (tournament_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [r["user_id"] for r in rows]

    async def count(self) -> int:
        async with self._conn.execute("SELECT COUNT(*) AS n FROM users") as cur:
            row = await cur.fetchone()
        return int(row["n"]) if row else 0

    async def list_page(self, offset: int, limit: int) -> list[User]:
        async with self._conn.execute(
            "SELECT user_id, username, first_name, is_blocked, is_banned, created_at "
            "FROM users ORDER BY created_at DESC, user_id DESC "
            "LIMIT ? OFFSET ?",
            (limit, offset),
        ) as cur:
            rows = await cur.fetchall()
        return [_row_to_user(r) for r in rows]

    async def search(self, query: str, limit: int = 50) -> list[User]:
        """Search by username/first_name substring (case-insensitive) and exact user_id."""
        q = query.strip()
        if not q:
            return []
        like = f"%{q.lower()}%"
        params: tuple = (like, like)
        sql = (
            "SELECT user_id, username, first_name, is_blocked, is_banned, created_at "
            "FROM users "
            "WHERE LOWER(IFNULL(username, '')) LIKE ? "
            "   OR LOWER(IFNULL(first_name, '')) LIKE ?"
        )
        if q.isdigit():
            sql += " OR user_id = ?"
            params = (like, like, int(q))
        sql += " ORDER BY created_at DESC, user_id DESC LIMIT ?"
        params = params + (limit,)
        async with self._conn.execute(sql, params) as cur:
            rows = await cur.fetchall()
        return [_row_to_user(r) for r in rows]


def _row_to_user(row: aiosqlite.Row) -> User:
    return User(
        user_id=row["user_id"],
        username=row["username"],
        first_name=row["first_name"],
        is_blocked=bool(row["is_blocked"]),
        is_banned=bool(row["is_banned"]),
        created_at=row["created_at"],
    )
