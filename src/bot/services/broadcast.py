from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

from bot.repositories import UsersRepo

log = logging.getLogger(__name__)

# Запас от лимита Telegram ~30 msg/sec
DEFAULT_RATE_PER_SEC = 25


@dataclass
class BroadcastResult:
    sent: int = 0
    blocked: int = 0
    errors: int = 0


async def get_recipients(
    users_repo: UsersRepo,
    tournament_id: int | None,
) -> list[int]:
    if tournament_id is None:
        return await users_repo.all_active_ids()
    return await users_repo.subscribed_active_ids(tournament_id)


async def broadcast(
    bot: Bot,
    users_repo: UsersRepo,
    recipients: list[int],
    source_chat_id: int,
    source_message_id: int,
    *,
    rate_per_sec: int = DEFAULT_RATE_PER_SEC,
) -> BroadcastResult:
    """Copy a source message to each recipient with rate-limiting and error handling."""
    result = BroadcastResult()
    delay = 1.0 / max(rate_per_sec, 1)

    for user_id in recipients:
        await _send_one(bot, users_repo, user_id, source_chat_id, source_message_id, result)
        await asyncio.sleep(delay)

    log.info(
        "broadcast finished: sent=%d blocked=%d errors=%d",
        result.sent,
        result.blocked,
        result.errors,
    )
    return result


async def _send_one(
    bot: Bot,
    users_repo: UsersRepo,
    user_id: int,
    source_chat_id: int,
    source_message_id: int,
    result: BroadcastResult,
) -> None:
    try:
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=source_chat_id,
            message_id=source_message_id,
        )
        result.sent += 1
    except TelegramRetryAfter as e:
        log.warning("rate limited, sleeping %s seconds", e.retry_after)
        await asyncio.sleep(e.retry_after)
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=source_chat_id,
                message_id=source_message_id,
            )
            result.sent += 1
        except Exception:
            log.exception("retry after RetryAfter failed for user_id=%s", user_id)
            result.errors += 1
    except TelegramForbiddenError:
        await users_repo.mark_blocked(user_id)
        result.blocked += 1
    except TelegramBadRequest as e:
        msg = (e.message or "").lower()
        if "chat not found" in msg or "user is deactivated" in msg or "blocked" in msg:
            await users_repo.mark_blocked(user_id)
            result.blocked += 1
        else:
            log.exception("bad request for user_id=%s", user_id)
            result.errors += 1
    except Exception:
        log.exception("unexpected error for user_id=%s", user_id)
        result.errors += 1
