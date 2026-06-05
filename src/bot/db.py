from __future__ import annotations

import aiosqlite

CURRENT_SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    is_blocked  INTEGER NOT NULL DEFAULT 0,
    is_banned   INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tournaments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscriptions (
    user_id       INTEGER NOT NULL,
    tournament_id INTEGER NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, tournament_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_tournament
    ON subscriptions(tournament_id);

CREATE INDEX IF NOT EXISTS idx_tournaments_active
    ON tournaments(is_active);

CREATE TABLE IF NOT EXISTS inquiry_recipients (
    inquiry_type TEXT NOT NULL,
    user_id      INTEGER NOT NULL,
    added_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (inquiry_type, user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_inquiry_recipients_type
    ON inquiry_recipients(inquiry_type);
"""


async def connect(db_path: str) -> aiosqlite.Connection:
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.executescript(SCHEMA)
    await _migrate(conn)
    await conn.commit()
    return conn


async def _migrate(conn: aiosqlite.Connection) -> None:
    async with conn.execute("PRAGMA user_version") as cur:
        row = await cur.fetchone()
        version = row[0] if row else 0

    if version < 1:
        # Add is_banned column to existing users tables that were created before v1.
        await _add_column_if_missing(
            conn, "users", "is_banned", "INTEGER NOT NULL DEFAULT 0"
        )
        await conn.execute("PRAGMA user_version = 1")

    if version < 2:
        # v2: inquiry_recipients is created via CREATE TABLE IF NOT EXISTS in SCHEMA above.
        # Nothing extra to do for existing DBs.
        await conn.execute("PRAGMA user_version = 2")


async def _add_column_if_missing(
    conn: aiosqlite.Connection, table: str, column: str, definition: str
) -> None:
    async with conn.execute(f"PRAGMA table_info({table})") as cur:
        rows = await cur.fetchall()
    existing = {r["name"] for r in rows}
    if column not in existing:
        await conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
