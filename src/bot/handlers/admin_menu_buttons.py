from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.keyboards import admin as admin_kb
from bot.keyboards.callbacks import AdminCB, MenuBtnCB
from bot.middlewares.admin_only import AdminOnlyMiddleware
from bot.repositories import MenuButton, MenuButtonsRepo
from bot.states import AddMenuButton, EditMenuButtonText, EditMenuButtonUrl

router = Router(name="admin_menu_buttons")
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())


def _is_valid_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _render_card(b: MenuButton) -> str:
    return texts.MENU_BUTTON_CARD.format(
        id=b.id,
        text=html.escape(b.text),
        url=html.escape(b.url),
    )


# ---------- список ----------

@router.callback_query(AdminCB.filter(F.action == "menu_buttons"))
async def cb_menu_buttons_entry(
    callback: CallbackQuery,
    state: FSMContext,
    menu_buttons_repo: MenuButtonsRepo,
) -> None:
    await state.clear()
    await _show_list(callback, menu_buttons_repo)


@router.callback_query(MenuBtnCB.filter(F.action == "list"))
async def cb_menu_buttons_list(
    callback: CallbackQuery,
    state: FSMContext,
    menu_buttons_repo: MenuButtonsRepo,
) -> None:
    await state.clear()
    await _show_list(callback, menu_buttons_repo)


async def _show_list(callback: CallbackQuery, menu_buttons_repo: MenuButtonsRepo) -> None:
    buttons = await menu_buttons_repo.list_all()
    text = (
        texts.MENU_BUTTONS_LIST_HEADER.format(n=len(buttons))
        if buttons
        else texts.MENU_BUTTONS_LIST_EMPTY
    )
    await callback.message.edit_text(
        text, reply_markup=admin_kb.menu_buttons_list(buttons)
    )
    await callback.answer()


# ---------- карточка кнопки ----------

@router.callback_query(MenuBtnCB.filter(F.action == "view"))
async def cb_menu_button_view(
    callback: CallbackQuery,
    callback_data: MenuBtnCB,
    state: FSMContext,
    menu_buttons_repo: MenuButtonsRepo,
) -> None:
    await state.clear()
    b = await menu_buttons_repo.get(callback_data.button_id)
    if b is None:
        await callback.answer("Кнопка не найдена", show_alert=True)
        return
    buttons = await menu_buttons_repo.list_all()
    ids = [x.id for x in buttons]
    is_first = ids[0] == b.id if ids else True
    is_last = ids[-1] == b.id if ids else True
    await callback.message.edit_text(
        _render_card(b),
        reply_markup=admin_kb.menu_button_card(b, is_first=is_first, is_last=is_last),
    )
    await callback.answer()


# ---------- добавление ----------

@router.callback_query(MenuBtnCB.filter(F.action == "add"))
async def cb_menu_button_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddMenuButton.waiting_for_text)
    await callback.message.edit_text(texts.MENU_BUTTON_ENTER_TEXT)
    await callback.answer()


@router.message(AddMenuButton.waiting_for_text)
async def msg_add_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer(texts.MENU_BUTTON_TEXT_EMPTY)
        return
    await state.update_data(text=text)
    await state.set_state(AddMenuButton.waiting_for_url)
    await message.answer(texts.MENU_BUTTON_ENTER_URL)


@router.message(AddMenuButton.waiting_for_url)
async def msg_add_url(
    message: Message,
    state: FSMContext,
    menu_buttons_repo: MenuButtonsRepo,
) -> None:
    url = (message.text or "").strip()
    if not _is_valid_url(url):
        await message.answer(texts.MENU_BUTTON_INVALID_URL)
        return
    data = await state.get_data()
    await menu_buttons_repo.create(text=data["text"], url=url)
    await state.clear()
    await message.answer(texts.MENU_BUTTON_ADDED)
    buttons = await menu_buttons_repo.list_all()
    await message.answer(
        texts.MENU_BUTTONS_LIST_HEADER.format(n=len(buttons)),
        reply_markup=admin_kb.menu_buttons_list(buttons),
    )


# ---------- редактирование текста ----------

@router.callback_query(MenuBtnCB.filter(F.action == "edit_text"))
async def cb_edit_text(
    callback: CallbackQuery,
    callback_data: MenuBtnCB,
    state: FSMContext,
) -> None:
    await state.set_state(EditMenuButtonText.waiting_for_value)
    await state.update_data(button_id=callback_data.button_id)
    await callback.message.edit_text(texts.MENU_BUTTON_ENTER_TEXT)
    await callback.answer()


@router.message(EditMenuButtonText.waiting_for_value)
async def msg_edit_text(
    message: Message,
    state: FSMContext,
    menu_buttons_repo: MenuButtonsRepo,
) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer(texts.MENU_BUTTON_TEXT_EMPTY)
        return
    data = await state.get_data()
    button_id: int = data["button_id"]
    await menu_buttons_repo.update_text(button_id, text)
    await state.clear()
    await message.answer(texts.MENU_BUTTON_UPDATED)
    await _send_card(message, menu_buttons_repo, button_id)


# ---------- редактирование URL ----------

@router.callback_query(MenuBtnCB.filter(F.action == "edit_url"))
async def cb_edit_url(
    callback: CallbackQuery,
    callback_data: MenuBtnCB,
    state: FSMContext,
) -> None:
    await state.set_state(EditMenuButtonUrl.waiting_for_value)
    await state.update_data(button_id=callback_data.button_id)
    await callback.message.edit_text(texts.MENU_BUTTON_ENTER_URL)
    await callback.answer()


@router.message(EditMenuButtonUrl.waiting_for_value)
async def msg_edit_url(
    message: Message,
    state: FSMContext,
    menu_buttons_repo: MenuButtonsRepo,
) -> None:
    url = (message.text or "").strip()
    if not _is_valid_url(url):
        await message.answer(texts.MENU_BUTTON_INVALID_URL)
        return
    data = await state.get_data()
    button_id: int = data["button_id"]
    await menu_buttons_repo.update_url(button_id, url)
    await state.clear()
    await message.answer(texts.MENU_BUTTON_UPDATED)
    await _send_card(message, menu_buttons_repo, button_id)


# ---------- порядок ----------

@router.callback_query(MenuBtnCB.filter(F.action == "up"))
async def cb_move_up(
    callback: CallbackQuery,
    callback_data: MenuBtnCB,
    menu_buttons_repo: MenuButtonsRepo,
) -> None:
    await menu_buttons_repo.move_up(callback_data.button_id)
    await callback.answer()
    await _refresh_card(callback, menu_buttons_repo, callback_data.button_id)


@router.callback_query(MenuBtnCB.filter(F.action == "down"))
async def cb_move_down(
    callback: CallbackQuery,
    callback_data: MenuBtnCB,
    menu_buttons_repo: MenuButtonsRepo,
) -> None:
    await menu_buttons_repo.move_down(callback_data.button_id)
    await callback.answer()
    await _refresh_card(callback, menu_buttons_repo, callback_data.button_id)


# ---------- удаление ----------

@router.callback_query(MenuBtnCB.filter(F.action == "del"))
async def cb_del_confirm(
    callback: CallbackQuery,
    callback_data: MenuBtnCB,
    menu_buttons_repo: MenuButtonsRepo,
) -> None:
    b = await menu_buttons_repo.get(callback_data.button_id)
    if b is None:
        await callback.answer("Кнопка не найдена", show_alert=True)
        return
    await callback.message.edit_text(
        texts.MENU_BUTTON_DELETE_CONFIRM.format(text=html.escape(b.text)),
        reply_markup=admin_kb.menu_button_delete_confirm(b.id),
    )
    await callback.answer()


@router.callback_query(MenuBtnCB.filter(F.action == "del_yes"))
async def cb_del_yes(
    callback: CallbackQuery,
    callback_data: MenuBtnCB,
    menu_buttons_repo: MenuButtonsRepo,
) -> None:
    await menu_buttons_repo.delete(callback_data.button_id)
    await callback.answer(texts.MENU_BUTTON_DELETED)
    await _show_list(callback, menu_buttons_repo)


# ---------- helpers ----------

async def _refresh_card(
    callback: CallbackQuery, menu_buttons_repo: MenuButtonsRepo, button_id: int
) -> None:
    b = await menu_buttons_repo.get(button_id)
    if b is None:
        await _show_list(callback, menu_buttons_repo)
        return
    buttons = await menu_buttons_repo.list_all()
    ids = [x.id for x in buttons]
    is_first = ids[0] == b.id
    is_last = ids[-1] == b.id
    await callback.message.edit_text(
        _render_card(b),
        reply_markup=admin_kb.menu_button_card(b, is_first=is_first, is_last=is_last),
    )


async def _send_card(
    message: Message, menu_buttons_repo: MenuButtonsRepo, button_id: int
) -> None:
    b = await menu_buttons_repo.get(button_id)
    if b is None:
        buttons = await menu_buttons_repo.list_all()
        await message.answer(
            texts.MENU_BUTTONS_LIST_HEADER.format(n=len(buttons)),
            reply_markup=admin_kb.menu_buttons_list(buttons),
        )
        return
    buttons = await menu_buttons_repo.list_all()
    ids = [x.id for x in buttons]
    is_first = ids[0] == b.id
    is_last = ids[-1] == b.id
    await message.answer(
        _render_card(b),
        reply_markup=admin_kb.menu_button_card(b, is_first=is_first, is_last=is_last),
    )
