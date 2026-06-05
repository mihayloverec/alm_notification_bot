from aiogram import Dispatcher

from . import (
    admin,
    admin_inquiry,
    admin_menu_buttons,
    admin_organizers,
    admin_players,
    broadcast,
    common,
    inquiry,
    user,
)


def register_all(dp: Dispatcher) -> None:
    dp.include_router(common.router)
    dp.include_router(broadcast.router)
    dp.include_router(admin_inquiry.router)
    dp.include_router(admin_menu_buttons.router)
    dp.include_router(admin_organizers.router)
    dp.include_router(admin_players.router)
    dp.include_router(admin.router)
    dp.include_router(inquiry.router)
    dp.include_router(user.router)
