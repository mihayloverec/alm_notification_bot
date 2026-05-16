from __future__ import annotations

import aiosqlite


class SubscriptionsRepo:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def subscribe(self, user_id: int, tournament_id: int) -> None:
        await self._conn.execute(
            "INSERT OR IGNORE INTO subscriptions (user_id, tournament_id) VALUES (?, ?)",
            (user_id, tournament_id),
        )
        await self._conn.commit()

    async def unsubscribe(self, user_id: int, tournament_id: int) -> None:
        await self._conn.execute(
            "DELETE FROM subscriptions WHERE user_id = ? AND tournament_id = ?",
            (user_id, tournament_id),
        )
        await self._conn.commit()

    async def is_subscribed(self, user_id: int, tournament_id: int) -> bool:
        async with self._conn.execute(
            "SELECT 1 FROM subscriptions WHERE user_id = ? AND tournament_id = ?",
            (user_id, tournament_id),
        ) as cur:
            return await cur.fetchone() is not None

    async def list_user_tournament_ids(self, user_id: int) -> list[int]:
        async with self._conn.execute(
            "SELECT tournament_id FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [r["tournament_id"] for r in rows]

    async def count_for_user(self, user_id: int) -> int:
        async with self._conn.execute(
            "SELECT COUNT(*) AS n FROM subscriptions WHERE user_id = ?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
        return int(row["n"]) if row else 0
