from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.config import Config
from bot.keyboards import user as user_kb
from bot.keyboards.callbacks import MenuCB
from bot.repositories import OrganizersRepo, UsersRepo

router = Router(name="common")


async def _is_elevated(
    user_id: int, config: Config, organizers_repo: OrganizersRepo
) -> bool:
    return config.is_admin(user_id) or await organizers_repo.is_organizer(user_id)


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    users_repo: UsersRepo,
    organizers_repo: OrganizersRepo,
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
    elevated = await _is_elevated(user.id, config, organizers_repo)
    await message.answer(
        texts.START_GREETING,
        reply_markup=user_kb.main_menu(elevated=elevated),
    )


@router.callback_query(MenuCB.filter(F.action == "main"))
async def cb_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
    config: Config,
    organizers_repo: OrganizersRepo,
) -> None:
    await state.clear()
    user = callback.from_user
    elevated = await _is_elevated(user.id, config, organizers_repo)
    await callback.message.edit_text(
        texts.MAIN_MENU,
        reply_markup=user_kb.main_menu(elevated=elevated),
    )
    await callback.answer()
