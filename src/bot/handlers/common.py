from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.config import Config
from bot.keyboards import user as user_kb
from bot.keyboards.callbacks import MenuCB
from bot.repositories import UsersRepo

router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    users_repo: UsersRepo,
    config: Config,
) -> None:
    await state.clear()
    user = message.from_user
    if user is None:
        return
    await users_repo.upsert(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )
    await message.answer(
        texts.START_GREETING,
        reply_markup=user_kb.main_menu(is_admin=config.is_admin(user.id)),
    )


@router.callback_query(MenuCB.filter(F.action == "main"))
async def cb_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
    config: Config,
) -> None:
    await state.clear()
    user = callback.from_user
    await callback.message.edit_text(
        texts.MAIN_MENU,
        reply_markup=user_kb.main_menu(is_admin=config.is_admin(user.id)),
    )
    await callback.answer()
