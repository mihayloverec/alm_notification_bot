from __future__ import annotations

from dataclasses import dataclass

import aiosqlite


@dataclass(frozen=True)
class Tournament:
    id: int
    name: str
    description: str
    is_active: bool


class TournamentsRepo:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(self, name: str, description: str) -> int:
        cur = await self._conn.execute(
            "INSERT INTO tournaments (name, description, is_active) VALUES (?, ?, 1)",
            (name, description),
        )
        await self._conn.commit()
        return cur.lastrowid

    async def get(self, tournament_id: int) -> Tournament | None:
        async with self._conn.execute(
            "SELECT id, name, description, is_active FROM tournaments WHERE id = ?",
            (tournament_id,),
        ) as cur:
            row = await cur.fetchone()
        return _row_to_tournament(row) if row else None

    async def list_active(self) -> list[Tournament]:
        async with self._conn.execute(
            "SELECT id, name, description, is_active FROM tournaments "
            "WHERE is_active = 1 ORDER BY created_at DESC, id DESC"
        ) as cur:
            rows = await cur.fetchall()
        return [_row_to_tournament(r) for r in rows]

    async def list_all(self) -> list[Tournament]:
        async with self._conn.execute(
            "SELECT id, name, description, is_active FROM tournaments "
            "ORDER BY is_active DESC, created_at DESC, id DESC"
        ) as cur:
            rows = await cur.fetchall()
        return [_row_to_tournament(r) for r in rows]

    async def set_name(self, tournament_id: int, name: str) -> None:
        await self._conn.execute(
            "UPDATE tournaments SET name = ? WHERE id = ?",
            (name, tournament_id),
        )
        await self._conn.commit()

    async def set_description(self, tournament_id: int, description: str) -> None:
        await self._conn.execute(
            "UPDATE tournaments SET description = ? WHERE id = ?",
            (description, tournament_id),
        )
        await self._conn.commit()

    async def set_active(self, tournament_id: int, is_active: bool) -> None:
        await self._conn.execute(
            "UPDATE tournaments SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, tournament_id),
        )
        await self._conn.commit()


def _row_to_tournament(row: aiosqlite.Row) -> Tournament:
    return Tournament(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        is_active=bool(row["is_active"]),
    )
