from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot import db
from bot.config import load_config
from bot.handlers import register_all
from bot.middlewares.ban_check import BanCheckMiddleware
from bot.middlewares.deps import DepsMiddleware
from bot.repositories import (
    InquiryRecipientsRepo,
    MenuButtonsRepo,
    OrganizersRepo,
    SubscriptionsRepo,
    TournamentsRepo,
    UsersRepo,
)


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


async def main() -> None:
    config = load_config()
    setup_logging(config.log_level)
    log = logging.getLogger("bot")

    os.makedirs(os.path.dirname(config.db_path) or ".", exist_ok=True)
    conn = await db.connect(config.db_path)

    users_repo = UsersRepo(conn)
    tournaments_repo = TournamentsRepo(conn)
    subscriptions_repo = SubscriptionsRepo(conn)
    inquiry_recipients_repo = InquiryRecipientsRepo(conn)
    organizers_repo = OrganizersRepo(conn)
    menu_buttons_repo = MenuButtonsRepo(conn)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    deps = DepsMiddleware(
        config=config,
        users_repo=users_repo,
        tournaments_repo=tournaments_repo,
        subscriptions_repo=subscriptions_repo,
        inquiry_recipients_repo=inquiry_recipients_repo,
        organizers_repo=organizers_repo,
        menu_buttons_repo=menu_buttons_repo,
    )
    dp.message.middleware(deps)
    dp.callback_query.middleware(deps)

    ban_check = BanCheckMiddleware()
    dp.message.middleware(ban_check)
    dp.callback_query.middleware(ban_check)

    register_all(dp)

    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="menu", description="Главное меню"),
    ])

    log.info("starting bot, admins=%s", sorted(config.admin_ids))
    try:
        await dp.start_polling(bot, handle_signals=True)
    finally:
        await conn.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
