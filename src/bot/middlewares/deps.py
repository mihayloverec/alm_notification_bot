from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.config import Config
from bot.repositories import (
    InquiryRecipientsRepo,
    MenuButtonsRepo,
    OrganizersRepo,
    SubscriptionsRepo,
    TournamentsRepo,
    UsersRepo,
)


class DepsMiddleware(BaseMiddleware):
    """Injects config and repositories into handler kwargs."""

    def __init__(
        self,
        config: Config,
        users_repo: UsersRepo,
        tournaments_repo: TournamentsRepo,
        subscriptions_repo: SubscriptionsRepo,
        inquiry_recipients_repo: InquiryRecipientsRepo,
        organizers_repo: OrganizersRepo,
        menu_buttons_repo: MenuButtonsRepo,
    ) -> None:
        self._config = config
        self._users_repo = users_repo
        self._tournaments_repo = tournaments_repo
        self._subscriptions_repo = subscriptions_repo
        self._inquiry_recipients_repo = inquiry_recipients_repo
        self._organizers_repo = organizers_repo
        self._menu_buttons_repo = menu_buttons_repo

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
        data["inquiry_recipients_repo"] = self._inquiry_recipients_repo
        data["organizers_repo"] = self._organizers_repo
        data["menu_buttons_repo"] = self._menu_buttons_repo
        return await handler(event, data)
