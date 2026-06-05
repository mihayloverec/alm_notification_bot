from __future__ import annotations

import html
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.keyboards import admin as admin_kb
from bot.keyboards.callbacks import AdminCB, OrganizerCB
from bot.middlewares.admin_only import AdminOnlyMiddleware
from bot.repositories import OrganizersRepo, User, UsersRepo
from bot.states import AddOrganizer

router = Router(name="admin_organizers")
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())

PICK_PAGE_SIZE = 10


# ---------- список организаторов ----------

@router.callback_query(AdminCB.filter(F.action == "organizers"))
async def cb_organizers_entry(
    callback: CallbackQuery,
    state: FSMContext,
    organizers_repo: OrganizersRepo,
) -> None:
    await state.clear()
    await _show_list(callback, organizers_repo)


@router.callback_query(OrganizerCB.filter(F.action == "list"))
async def cb_organizers_list(
    callback: CallbackQuery,
    state: FSMContext,
    organizers_repo: OrganizersRepo,
) -> None:
    await state.clear()
    await _show_list(callback, organizers_repo)


async def _show_list(callback: CallbackQuery, organizers_repo: OrganizersRepo) -> None:
    users = await organizers_repo.list_users()
    text = (
        texts.ORGANIZERS_LIST_HEADER.format(n=len(users))
        if users
        else texts.ORGANIZERS_LIST_EMPTY
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_kb.organizers_list(users),
    )
    await callback.answer()


# ---------- добавление: picker ----------

@router.callback_query(OrganizerCB.filter(F.action == "add"))
async def cb_organizer_add_picker(
    callback: CallbackQuery,
    callback_data: OrganizerCB,
    users_repo: UsersRepo,
) -> None:
    await _show_pick_page(callback, users_repo, page=callback_data.page)


@router.callback_query(OrganizerCB.filter(F.action == "page"))
async def cb_organizer_page(
    callback: CallbackQuery,
    callback_data: OrganizerCB,
    users_repo: UsersRepo,
) -> None:
    await _show_pick_page(callback, users_repo, page=callback_data.page)


async def _show_pick_page(
    callback: CallbackQuery, users_repo: UsersRepo, *, page: int
) -> None:
    total = await users_repo.count()
    if total == 0:
        await callback.message.edit_text(
            texts.ORGANIZER_PICK_EMPTY,
            reply_markup=admin_kb.organizers_list([]),
        )
        await callback.answer()
        return
    pages = max(1, math.ceil(total / PICK_PAGE_SIZE))
    page = max(0, min(page, pages - 1))
    users = await users_repo.list_page(offset=page * PICK_PAGE_SIZE, limit=PICK_PAGE_SIZE)
    await callback.message.edit_text(
        texts.ORGANIZER_PICK_HEADER.format(page=page + 1, pages=pages),
        reply_markup=admin_kb.organizer_pick_list(users, page=page, pages=pages),
    )
    await callback.answer()


# ---------- добавление: поиск по @username / ID ----------

@router.callback_query(OrganizerCB.filter(F.action == "search"))
async def cb_organizer_search(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.set_state(AddOrganizer.waiting_for_query)
    await callback.message.edit_text(texts.ORGANIZER_SEARCH_PROMPT)
    await callback.answer()


@router.message(AddOrganizer.waiting_for_query)
async def msg_organizer_search_query(
    message: Message,
    state: FSMContext,
    users_repo: UsersRepo,
) -> None:
    raw = (message.text or "").strip()
    q = raw.lstrip("@")
    await state.clear()
    if not q:
        await message.answer(texts.ORGANIZER_SEARCH_NOT_FOUND.format(q=""))
        return
    results = await users_repo.search(q)
    if not results:
        await message.answer(
            texts.ORGANIZER_SEARCH_NOT_FOUND.format(q=html.escape(raw)),
            reply_markup=admin_kb.organizer_search_results([]),
        )
        return
    await message.answer(
        texts.ORGANIZER_SEARCH_RESULTS.format(n=len(results)),
        reply_markup=admin_kb.organizer_search_results(results),
    )


# ---------- выбор кандидата ----------

@router.callback_query(OrganizerCB.filter(F.action == "pick"))
async def cb_organizer_pick(
    callback: CallbackQuery,
    callback_data: OrganizerCB,
    organizers_repo: OrganizersRepo,
) -> None:
    already = await organizers_repo.is_organizer(callback_data.user_id)
    await organizers_repo.add(callback_data.user_id)
    await callback.answer(
        texts.ORGANIZER_ALREADY if already else texts.ORGANIZER_ADDED
    )
    await _show_list(callback, organizers_repo)


# ---------- удаление ----------

@router.callback_query(OrganizerCB.filter(F.action == "del"))
async def cb_organizer_del_confirm(
    callback: CallbackQuery,
    callback_data: OrganizerCB,
    users_repo: UsersRepo,
) -> None:
    u = await users_repo.get(callback_data.user_id)
    who = _descr(u) if u is not None else f"id:{callback_data.user_id}"
    await callback.message.edit_text(
        texts.ORGANIZER_REMOVE_CONFIRM.format(who=who),
        reply_markup=admin_kb.organizer_remove_confirm(callback_data.user_id),
    )
    await callback.answer()


@router.callback_query(OrganizerCB.filter(F.action == "del_yes"))
async def cb_organizer_del_yes(
    callback: CallbackQuery,
    callback_data: OrganizerCB,
    organizers_repo: OrganizersRepo,
) -> None:
    await organizers_repo.remove(callback_data.user_id)
    await callback.answer(texts.ORGANIZER_REMOVED)
    await _show_list(callback, organizers_repo)


def _descr(u: User) -> str:
    if u.username:
        return f"@{html.escape(u.username)}"
    if u.first_name:
        return html.escape(u.first_name)
    return f"id:{u.user_id}"
