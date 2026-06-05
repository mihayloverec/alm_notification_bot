from __future__ import annotations

from dataclasses import dataclass

import aiosqlite


@dataclass(frozen=True)
class MenuButton:
    id: int
    text: str
    url: str
    sort_order: int


class MenuButtonsRepo:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(self, text: str, url: str) -> int:
        async with self._conn.execute(
            "SELECT COALESCE(MAX(sort_order), 0) AS m FROM menu_buttons"
        ) as cur:
            row = await cur.fetchone()
        next_order = (row["m"] if row else 0) + 1
        cur = await self._conn.execute(
            "INSERT INTO menu_buttons (text, url, sort_order) VALUES (?, ?, ?)",
            (text, url, next_order),
        )
        await self._conn.commit()
        return cur.lastrowid

    async def update_text(self, button_id: int, text: str) -> None:
        await self._conn.execute(
            "UPDATE menu_buttons SET text = ? WHERE id = ?",
            (text, button_id),
        )
        await self._conn.commit()

    async def update_url(self, button_id: int, url: str) -> None:
        await self._conn.execute(
            "UPDATE menu_buttons SET url = ? WHERE id = ?",
            (url, button_id),
        )
        await self._conn.commit()

    async def delete(self, button_id: int) -> None:
        await self._conn.execute(
            "DELETE FROM menu_buttons WHERE id = ?",
            (button_id,),
        )
        await self._conn.commit()

    async def get(self, button_id: int) -> MenuButton | None:
        async with self._conn.execute(
            "SELECT id, text, url, sort_order FROM menu_buttons WHERE id = ?",
            (button_id,),
        ) as cur:
            row = await cur.fetchone()
        return _row_to_button(row) if row else None

    async def list_all(self) -> list[MenuButton]:
        async with self._conn.execute(
            "SELECT id, text, url, sort_order FROM menu_buttons "
            "ORDER BY sort_order ASC, id ASC"
        ) as cur:
            rows = await cur.fetchall()
        return [_row_to_button(r) for r in rows]

    async def move_up(self, button_id: int) -> None:
        """Swap sort_order with the predecessor (the one immediately above)."""
        await self._swap_with_neighbour(button_id, direction="up")

    async def move_down(self, button_id: int) -> None:
        """Swap sort_order with the successor (the one immediately below)."""
        await self._swap_with_neighbour(button_id, direction="down")

    async def _swap_with_neighbour(self, button_id: int, *, direction: str) -> None:
        target = await self.get(button_id)
        if target is None:
            return

        if direction == "up":
            sql = (
                "SELECT id, sort_order FROM menu_buttons "
                "WHERE sort_order < ? ORDER BY sort_order DESC LIMIT 1"
            )
        else:
            sql = (
                "SELECT id, sort_order FROM menu_buttons "
                "WHERE sort_order > ? ORDER BY sort_order ASC LIMIT 1"
            )
        async with self._conn.execute(sql, (target.sort_order,)) as cur:
            neighbour = await cur.fetchone()
        if neighbour is None:
            return

        await self._conn.execute(
            "UPDATE menu_buttons SET sort_order = ? WHERE id = ?",
            (neighbour["sort_order"], target.id),
        )
        await self._conn.execute(
            "UPDATE menu_buttons SET sort_order = ? WHERE id = ?",
            (target.sort_order, neighbour["id"]),
        )
        await self._conn.commit()


def _row_to_button(row: aiosqlite.Row) -> MenuButton:
    return MenuButton(
        id=row["id"],
        text=row["text"],
        url=row["url"],
        sort_order=row["sort_order"],
    )
