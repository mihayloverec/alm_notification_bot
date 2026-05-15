from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot import texts
from bot.config import Config


class AdminOnlyMiddleware(BaseMiddleware):
    """Allows event through only if from_user.id is in Config.admin_ids."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        config: Config = data["config"]
        user = getattr(event, "from_user", None)
        if user is None or not config.is_admin(user.id):
            if isinstance(event, CallbackQuery):
                await event.answer(texts.NOT_AUTHORIZED, show_alert=True)
            elif isinstance(event, Message):
                await event.answer(texts.NOT_AUTHORIZED)
            return None
        return await handler(event, data)
