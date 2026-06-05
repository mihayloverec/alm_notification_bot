from __future__ import annotations

import html
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot import texts
from bot.keyboards import admin as admin_kb
from bot.keyboards.callbacks import AdminCB, InquiryAdminCB
from bot.middlewares.admin_only import AdminOnlyMiddleware
from bot.repositories import (
    INQUIRY_TYPES,
    InquiryRecipientsRepo,
    User,
    UsersRepo,
)

router = Router(name="admin_inquiry")
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())

PICK_PAGE_SIZE = 10


# ---------- меню типов ----------

@router.callback_query(AdminCB.filter(F.action == "inquiry"))
async def cb_inquiry_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        texts.INQUIRY_ADMIN_MENU,
        reply_markup=admin_kb.inquiry_menu(),
    )
    await callback.answer()


@router.callback_query(InquiryAdminCB.filter(F.action == "menu"))
async def cb_inquiry_menu_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        texts.INQUIRY_ADMIN_MENU,
        reply_markup=admin_kb.inquiry_menu(),
    )
    await callback.answer()


# ---------- список получателей конкретного типа ----------

@router.callback_query(InquiryAdminCB.filter(F.action == "list"))
async def cb_inquiry_list(
    callback: CallbackQuery,
    callback_data: InquiryAdminCB,
    inquiry_recipients_repo: InquiryRecipientsRepo,
) -> None:
    inquiry_type = callback_data.type
    if inquiry_type not in INQUIRY_TYPES:
        await callback.answer()
        return

    label = texts.INQUIRY_LABEL[inquiry_type]
    users = await inquiry_recipients_repo.list_users(inquiry_type)
    if not users:
        text = texts.INQUIRY_ADMIN_LIST_EMPTY.format(label=label)
    else:
        text = texts.INQUIRY_ADMIN_LIST_HEADER.format(label=label, n=len(users))

    await callback.message.edit_text(
        text,
        reply_markup=admin_kb.inquiry_recipients_list(inquiry_type, users),
    )
    await callback.answer()


# ---------- добавление: picker по игрокам ----------

@router.callback_query(InquiryAdminCB.filter(F.action == "add"))
async def cb_inquiry_add(
    callback: CallbackQuery,
    callback_data: InquiryAdminCB,
    users_repo: UsersRepo,
) -> None:
    await _show_pick_page(
        callback, users_repo, inquiry_type=callback_data.type, page=callback_data.page
    )


@router.callback_query(InquiryAdminCB.filter(F.action == "page"))
async def cb_inquiry_page(
    callback: CallbackQuery,
    callback_data: InquiryAdminCB,
    users_repo: UsersRepo,
) -> None:
    await _show_pick_page(
        callback, users_repo, inquiry_type=callback_data.type, page=callback_data.page
    )


async def _show_pick_page(
    callback: CallbackQuery,
    users_repo: UsersRepo,
    *,
    inquiry_type: str,
    page: int,
) -> None:
    if inquiry_type not in INQUIRY_TYPES:
        await callback.answer()
        return

    label = texts.INQUIRY_LABEL[inquiry_type]
    total = await users_repo.count()
    if total == 0:
        await callback.message.edit_text(
            texts.INQUIRY_PICK_EMPTY,
            reply_markup=admin_kb.inquiry_recipients_list(inquiry_type, []),
        )
        await callback.answer()
        return

    pages = max(1, math.ceil(total / PICK_PAGE_SIZE))
    page = max(0, min(page, pages - 1))
    users = await users_repo.list_page(offset=page * PICK_PAGE_SIZE, limit=PICK_PAGE_SIZE)

    await callback.message.edit_text(
        texts.INQUIRY_PICK_HEADER.format(label=label, page=page + 1, pages=pages),
        reply_markup=admin_kb.inquiry_pick_list(
            inquiry_type, users, page=page, pages=pages
        ),
    )
    await callback.answer()


# ---------- выбор игрока в picker'е ----------

@router.callback_query(InquiryAdminCB.filter(F.action == "pick"))
async def cb_inquiry_pick(
    callback: CallbackQuery,
    callback_data: InquiryAdminCB,
    inquiry_recipients_repo: InquiryRecipientsRepo,
    users_repo: UsersRepo,
) -> None:
    inquiry_type = callback_data.type
    if inquiry_type not in INQUIRY_TYPES:
        await callback.answer()
        return

    label = texts.INQUIRY_LABEL[inquiry_type]
    already = await inquiry_recipients_repo.is_recipient(inquiry_type, callback_data.user_id)
    await inquiry_recipients_repo.add(inquiry_type, callback_data.user_id)

    if already:
        await callback.answer(texts.INQUIRY_RECIPIENT_ALREADY.format(label=label))
    else:
        await callback.answer(texts.INQUIRY_RECIPIENT_ADDED.format(label=label))

    users = await inquiry_recipients_repo.list_users(inquiry_type)
    text = texts.INQUIRY_ADMIN_LIST_HEADER.format(label=label, n=len(users))
    await callback.message.edit_text(
        text,
        reply_markup=admin_kb.inquiry_recipients_list(inquiry_type, users),
    )


# ---------- удаление получателя ----------

@router.callback_query(InquiryAdminCB.filter(F.action == "del"))
async def cb_inquiry_del_confirm(
    callback: CallbackQuery,
    callback_data: InquiryAdminCB,
    users_repo: UsersRepo,
) -> None:
    inquiry_type = callback_data.type
    if inquiry_type not in INQUIRY_TYPES:
        await callback.answer()
        return

    label = texts.INQUIRY_LABEL[inquiry_type]
    u = await users_repo.get(callback_data.user_id)
    who = _player_descr(u) if u is not None else f"id:{callback_data.user_id}"
    await callback.message.edit_text(
        texts.INQUIRY_RECIPIENT_REMOVE_CONFIRM.format(who=who, label=label),
        reply_markup=admin_kb.inquiry_remove_confirm(inquiry_type, callback_data.user_id),
    )
    await callback.answer()


@router.callback_query(InquiryAdminCB.filter(F.action == "del_yes"))
async def cb_inquiry_del_yes(
    callback: CallbackQuery,
    callback_data: InquiryAdminCB,
    inquiry_recipients_repo: InquiryRecipientsRepo,
) -> None:
    inquiry_type = callback_data.type
    if inquiry_type not in INQUIRY_TYPES:
        await callback.answer()
        return

    label = texts.INQUIRY_LABEL[inquiry_type]
    await inquiry_recipients_repo.remove(inquiry_type, callback_data.user_id)
    await callback.answer(texts.INQUIRY_RECIPIENT_REMOVED.format(label=label))

    users = await inquiry_recipients_repo.list_users(inquiry_type)
    if not users:
        text = texts.INQUIRY_ADMIN_LIST_EMPTY.format(label=label)
    else:
        text = texts.INQUIRY_ADMIN_LIST_HEADER.format(label=label, n=len(users))
    await callback.message.edit_text(
        text,
        reply_markup=admin_kb.inquiry_recipients_list(inquiry_type, users),
    )


def _player_descr(u: User) -> str:
    if u.username:
        return f"@{html.escape(u.username)}"
    if u.first_name:
        return html.escape(u.first_name)
    return f"id:{u.user_id}"
