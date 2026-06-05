from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot import texts
from bot.config import Config
from bot.repositories import OrganizersRepo


class ElevatedAccessMiddleware(BaseMiddleware):
    """Allows event through if user is admin (env) OR organizer (db)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return None

        config: Config = data["config"]
        if config.is_admin(user.id):
            return await handler(event, data)

        organizers_repo: OrganizersRepo = data["organizers_repo"]
        if await organizers_repo.is_organizer(user.id):
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer(texts.NOT_AUTHORIZED, show_alert=True)
        elif isinstance(event, Message):
            await event.answer(texts.NOT_AUTHORIZED)
        return None
