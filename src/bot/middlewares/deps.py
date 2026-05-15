from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.config import Config
from bot.repositories import SubscriptionsRepo, TournamentsRepo, UsersRepo


class DepsMiddleware(BaseMiddleware):
    """Injects config and repositories into handler kwargs."""

    def __init__(
        self,
        config: Config,
        users_repo: UsersRepo,
        tournaments_repo: TournamentsRepo,
        subscriptions_repo: SubscriptionsRepo,
    ) -> None:
        self._config = config
        self._users_repo = users_repo
        self._tournaments_repo = tournaments_repo
        self._subscriptions_repo = subscriptions_repo

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["config"] = self._config
        data["users_repo"] = self._users_repo
        data["tournaments_repo"] = self._tournaments_repo
        data["subscriptions_repo"] = self._subscriptions_repo
        return await handler(event, data)
