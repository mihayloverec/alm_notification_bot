from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.keyboards import admin as admin_kb
from bot.keyboards.callbacks import AddTournamentCB, AdminCB, MenuCB, TournamentCB
from bot.middlewares.admin_only import AdminOnlyMiddleware
from bot.repositories import TournamentsRepo
from bot.states import AddTournament, EditTournamentDescription, EditTournamentName

router = Router(name="admin")
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())


# ---------- admin menu ----------

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.ADMIN_MENU, reply_markup=admin_kb.admin_menu())


@router.callback_query(MenuCB.filter(F.action == "admin"))
async def cb_admin_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(texts.ADMIN_MENU, reply_markup=admin_kb.admin_menu())
    await callback.answer()


# ---------- add tournament ----------

@router.callback_query(AdminCB.filter(F.action == "add"))
async def cb_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddTournament.waiting_for_name)
    await callback.message.edit_text(texts.ADD_ENTER_NAME)
    await callback.answer()


@router.message(AddTournament.waiting_for_name)
async def add_receive_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым. Введите ещё раз:")
        return
    await state.update_data(name=name)
    await state.set_state(AddTournament.waiting_for_description)
    await message.answer(texts.ADD_ENTER_DESCRIPTION)


@router.message(AddTournament.waiting_for_description)
async def add_receive_description(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пришлите описание текстом:")
        return
    description = message.html_text
    data = await state.update_data(description=description)
    card = texts.render_card(data["name"], description)
    await state.set_state(AddTournament.waiting_for_confirm)
    await message.answer(
        texts.ADD_PREVIEW.format(card=card),
        reply_markup=admin_kb.add_tournament_confirm(),
    )


@router.callback_query(
    AddTournament.waiting_for_confirm, AddTournamentCB.filter(F.action == "save")
)
async def cb_add_save(
    callback: CallbackQuery,
    state: FSMContext,
    tournaments_repo: TournamentsRepo,
) -> None:
    data = await state.get_data()
    await tournaments_repo.create(name=data["name"], description=data.get("description", ""))
    await state.clear()
    await callback.message.edit_text(texts.ADD_SAVED)
    await callback.message.answer(texts.ADMIN_MENU, reply_markup=admin_kb.admin_menu())
    await callback.answer()


@router.callback_query(
    AddTournament.waiting_for_confirm, AddTournamentCB.filter(F.action == "cancel")
)
async def cb_add_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(texts.CANCELLED)
    await callback.message.answer(texts.ADMIN_MENU, reply_markup=admin_kb.admin_menu())
    await callback.answer()


# ---------- manage tournaments ----------

@router.callback_query(AdminCB.filter(F.action == "manage"))
async def cb_manage_list(
    callback: CallbackQuery,
    state: FSMContext,
    tournaments_repo: TournamentsRepo,
) -> None:
    await state.clear()
    tournaments = await tournaments_repo.list_all()
    if not tournaments:
        await callback.message.edit_text(
            "Турниров нет.",
            reply_markup=admin_kb.admin_menu(),
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        "Все турниры:",
        reply_markup=admin_kb.manage_list(tournaments),
    )
    await callback.answer()


@router.callback_query(TournamentCB.filter(F.action == "manage"))
async def cb_manage_card(
    callback: CallbackQuery,
    callback_data: TournamentCB,
    tournaments_repo: TournamentsRepo,
) -> None:
    t = await tournaments_repo.get(callback_data.tournament_id)
    if t is None:
        await callback.answer("Турнир не найден", show_alert=True)
        return
    text = texts.render_card(t.name, t.description, closed=not t.is_active)
    await callback.message.edit_text(text, reply_markup=admin_kb.manage_card(t))
    await callback.answer()


@router.callback_query(TournamentCB.filter(F.action == "toggle"))
async def cb_toggle_active(
    callback: CallbackQuery,
    callback_data: TournamentCB,
    tournaments_repo: TournamentsRepo,
) -> None:
    t = await tournaments_repo.get(callback_data.tournament_id)
    if t is None:
        await callback.answer("Турнир не найден", show_alert=True)
        return
    new_state = not t.is_active
    await tournaments_repo.set_active(t.id, new_state)
    await callback.answer(texts.TOURNAMENT_OPENED if new_state else texts.TOURNAMENT_CLOSED)
    t2 = await tournaments_repo.get(t.id)
    text = texts.render_card(t2.name, t2.description, closed=not t2.is_active)
    await callback.message.edit_text(text, reply_markup=admin_kb.manage_card(t2))


@router.callback_query(TournamentCB.filter(F.action == "edit_name"))
async def cb_edit_name_start(
    callback: CallbackQuery,
    callback_data: TournamentCB,
    state: FSMContext,
) -> None:
    await state.set_state(EditTournamentName.waiting_for_value)
    await state.update_data(tournament_id=callback_data.tournament_id)
    await callback.message.edit_text(texts.EDIT_ENTER_NAME)
    await callback.answer()


@router.message(EditTournamentName.waiting_for_value)
async def edit_name_receive(
    message: Message,
    state: FSMContext,
    tournaments_repo: TournamentsRepo,
) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым. Введите ещё раз:")
        return
    data = await state.get_data()
    tid: int = data["tournament_id"]
    await tournaments_repo.set_name(tid, name)
    await state.clear()
    t = await tournaments_repo.get(tid)
    await message.answer(texts.EDIT_SAVED)
    await message.answer(
        texts.render_card(t.name, t.description, closed=not t.is_active),
        reply_markup=admin_kb.manage_card(t),
    )


@router.callback_query(TournamentCB.filter(F.action == "edit_desc"))
async def cb_edit_desc_start(
    callback: CallbackQuery,
    callback_data: TournamentCB,
    state: FSMContext,
) -> None:
    await state.set_state(EditTournamentDescription.waiting_for_value)
    await state.update_data(tournament_id=callback_data.tournament_id)
    await callback.message.edit_text(texts.EDIT_ENTER_DESCRIPTION)
    await callback.answer()


@router.message(EditTournamentDescription.waiting_for_value)
async def edit_desc_receive(
    message: Message,
    state: FSMContext,
    tournaments_repo: TournamentsRepo,
) -> None:
    if not message.text:
        await message.answer("Пришлите описание текстом:")
        return
    description = message.html_text
    data = await state.get_data()
    tid: int = data["tournament_id"]
    await tournaments_repo.set_description(tid, description)
    await state.clear()
    t = await tournaments_repo.get(tid)
    await message.answer(texts.EDIT_SAVED)
    await message.answer(
        texts.render_card(t.name, t.description, closed=not t.is_active),
        reply_markup=admin_kb.manage_card(t),
    )
