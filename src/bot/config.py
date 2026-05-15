from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: frozenset[int]
    db_path: str
    log_level: str

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is required")

    raw_admins = os.getenv("ADMIN_IDS", "").strip()
    if not raw_admins:
        raise RuntimeError("ADMIN_IDS is required (comma-separated Telegram user_ids)")
    try:
        admin_ids = frozenset(int(x) for x in raw_admins.split(",") if x.strip())
    except ValueError as e:
        raise RuntimeError(f"ADMIN_IDS must contain integers: {e}") from e
    if not admin_ids:
        raise RuntimeError("ADMIN_IDS must contain at least one id")

    db_path = os.getenv("DB_PATH", "/app/data/bot.db").strip()
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    return Config(
        bot_token=bot_token,
        admin_ids=admin_ids,
        db_path=db_path,
        log_level=log_level,
    )
