from aiogram import Dispatcher

from . import admin, admin_players, broadcast, common, user


def register_all(dp: Dispatcher) -> None:
    dp.include_router(common.router)
    dp.include_router(broadcast.router)
    dp.include_router(admin_players.router)
    dp.include_router(admin.router)
    dp.include_router(user.router)
