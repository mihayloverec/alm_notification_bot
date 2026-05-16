from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot import texts
from bot.config import Config
from bot.repositories import UsersRepo


class BanCheckMiddleware(BaseMiddleware):
    """Blocks non-admin users with is_banned=1 from interacting with the bot."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        config: Config = data["config"]
        if config.is_admin(user.id):
            return await handler(event, data)

        users_repo: UsersRepo = data["users_repo"]
        u = await users_repo.get(user.id)
        if u is not None and u.is_banned:
            if isinstance(event, CallbackQuery):
                await event.answer(texts.BANNED_NOTICE, show_alert=True)
            elif isinstance(event, Message):
                await event.answer(texts.BANNED_NOTICE)
            return None

        return await handler(event, data)
