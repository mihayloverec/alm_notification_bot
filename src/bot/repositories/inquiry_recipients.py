from __future__ import annotations

import aiosqlite

from .users import User, _row_to_user

INQUIRY_SK = "sk"
INQUIRY_DK = "dk"
INQUIRY_TYPES = (INQUIRY_SK, INQUIRY_DK)


class InquiryRecipientsRepo:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def add(self, inquiry_type: str, user_id: int) -> None:
        await self._conn.execute(
            "INSERT OR IGNORE INTO inquiry_recipients (inquiry_type, user_id) VALUES (?, ?)",
            (inquiry_type, user_id),
        )
        await self._conn.commit()

    async def remove(self, inquiry_type: str, user_id: int) -> None:
        await self._conn.execute(
            "DELETE FROM inquiry_recipients WHERE inquiry_type = ? AND user_id = ?",
            (inquiry_type, user_id),
        )
        await self._conn.commit()

    async def is_recipient(self, inquiry_type: str, user_id: int) -> bool:
        async with self._conn.execute(
            "SELECT 1 FROM inquiry_recipients WHERE inquiry_type = ? AND user_id = ?",
            (inquiry_type, user_id),
        ) as cur:
            return await cur.fetchone() is not None

    async def has_any(self, inquiry_type: str) -> bool:
        async with self._conn.execute(
            "SELECT 1 FROM inquiry_recipients WHERE inquiry_type = ? LIMIT 1",
            (inquiry_type,),
        ) as cur:
            return await cur.fetchone() is not None

    async def list_users(self, inquiry_type: str) -> list[User]:
        async with self._conn.execute(
            """
            SELECT u.user_id, u.username, u.first_name, u.is_blocked, u.is_banned, u.created_at
            FROM inquiry_recipients ir
            JOIN users u ON u.user_id = ir.user_id
            WHERE ir.inquiry_type = ?
            ORDER BY ir.added_at ASC
            """,
            (inquiry_type,),
        ) as cur:
            rows = await cur.fetchall()
        return [_row_to_user(r) for r in rows]

    async def list_active_recipient_ids(self, inquiry_type: str) -> list[int]:
        """Recipients excluding banned and self-blocked — used for actual forwarding."""
        async with self._conn.execute(
            """
            SELECT ir.user_id
            FROM inquiry_recipients ir
            JOIN users u ON u.user_id = ir.user_id
            WHERE ir.inquiry_type = ? AND u.is_blocked = 0 AND u.is_banned = 0
            ORDER BY ir.added_at ASC
            """,
            (inquiry_type,),
        ) as cur:
            rows = await cur.fetchall()
        return [r["user_id"] for r in rows]
