from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot import texts
from bot.keyboards import admin as admin_kb
from bot.keyboards.callbacks import AdminCB, BroadcastBtnCB, BroadcastCB
from bot.middlewares.elevated import ElevatedAccessMiddleware
from bot.repositories import TournamentsRepo, UsersRepo
from bot.services import broadcast as broadcast_service
from bot.states import Broadcast

log = logging.getLogger(__name__)

router = Router(name="broadcast")
router.message.middleware(ElevatedAccessMiddleware())
router.callback_query.middleware(ElevatedAccessMiddleware())


@router.callback_query(AdminCB.filter(F.action == "broadcast"))
async def cb_broadcast_start(
    callback: CallbackQuery,
    state: FSMContext,
    tournaments_repo: TournamentsRepo,
) -> None:
    active = await tournaments_repo.list_active()
    await state.set_state(Broadcast.waiting_for_audience)
    await callback.message.edit_text(
        texts.BROADCAST_CHOOSE_AUDIENCE,
        reply_markup=admin_kb.broadcast_audience(active),
    )
    await callback.answer()


@router.callback_query(
    Broadcast.waiting_for_audience, BroadcastCB.filter(F.action == "cancel")
)
async def cb_broadcast_cancel_audience(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(texts.CANCELLED)
    await callback.message.answer(texts.ADMIN_MENU, reply_markup=admin_kb.admin_menu())
    await callback.answer()


@router.callback_query(
    Broadcast.waiting_for_audience, BroadcastCB.filter(F.action == "all")
)
async def cb_broadcast_audience_all(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(tournament_id=None)
    await state.set_state(Broadcast.waiting_for_message)
    await callback.message.edit_text(texts.BROADCAST_SEND_MESSAGE)
    await callback.answer()


@router.callback_query(
    Broadcast.waiting_for_audience, BroadcastCB.filter(F.action == "tournament")
)
async def cb_broadcast_audience_tournament(
    callback: CallbackQuery,
    callback_data: BroadcastCB,
    state: FSMContext,
) -> None:
    await state.update_data(tournament_id=callback_data.tournament_id)
    await state.set_state(Broadcast.waiting_for_message)
    await callback.message.edit_text(texts.BROADCAST_SEND_MESSAGE)
    await callback.answer()


@router.message(Broadcast.waiting_for_message)
async def receive_broadcast_message(
    message: Message,
    state: FSMContext,
    users_repo: UsersRepo,
) -> None:
    data = await state.get_data()
    tournament_id: int | None = data.get("tournament_id")
    recipients = await broadcast_service.get_recipients(users_repo, tournament_id)
    if not recipients:
        await state.clear()
        await message.answer(texts.BROADCAST_NO_RECIPIENTS)
        await message.answer(texts.ADMIN_MENU, reply_markup=admin_kb.admin_menu())
        return

    await state.update_data(
        source_chat_id=message.chat.id,
        source_message_id=message.message_id,
        recipients=recipients,
        buttons=[],
    )
    await state.set_state(Broadcast.waiting_for_confirm)
    await message.answer(
        texts.BROADCAST_PREVIEW_WITH_BUTTONS.format(count=len(recipients), buttons=0),
        reply_markup=admin_kb.broadcast_confirm(buttons_count=0),
    )


# ---------- управление кнопками в превью ----------

@router.callback_query(
    Broadcast.waiting_for_confirm, BroadcastBtnCB.filter(F.action == "add")
)
async def cb_broadcast_button_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Broadcast.waiting_for_button_text)
    await callback.message.edit_text(texts.BROADCAST_BUTTON_ENTER_TEXT)
    await callback.answer()


@router.message(Broadcast.waiting_for_button_text)
async def msg_broadcast_button_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer(texts.MENU_BUTTON_TEXT_EMPTY)
        return
    await state.update_data(_pending_btn_text=text)
    await state.set_state(Broadcast.waiting_for_button_url)
    await message.answer(texts.BROADCAST_BUTTON_ENTER_URL)


@router.message(Broadcast.waiting_for_button_url)
async def msg_broadcast_button_url(message: Message, state: FSMContext) -> None:
    url = (message.text or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer(texts.MENU_BUTTON_INVALID_URL)
        return
    data = await state.get_data()
    buttons: list[list[str]] = list(data.get("buttons", []))
    buttons.append([data["_pending_btn_text"], url])
    await state.update_data(buttons=buttons, _pending_btn_text=None)
    await state.set_state(Broadcast.waiting_for_confirm)
    await message.answer(
        texts.BROADCAST_PREVIEW_WITH_BUTTONS.format(
            count=len(data["recipients"]), buttons=len(buttons)
        ),
        reply_markup=admin_kb.broadcast_confirm(buttons_count=len(buttons)),
    )


@router.callback_query(
    Broadcast.waiting_for_confirm, BroadcastBtnCB.filter(F.action == "reset")
)
async def cb_broadcast_buttons_reset(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(buttons=[])
    await callback.answer(texts.BROADCAST_BUTTONS_RESET)
    await callback.message.edit_text(
        texts.BROADCAST_PREVIEW_WITH_BUTTONS.format(
            count=len(data["recipients"]), buttons=0
        ),
        reply_markup=admin_kb.broadcast_confirm(buttons_count=0),
    )


@router.callback_query(
    Broadcast.waiting_for_confirm, BroadcastCB.filter(F.action == "cancel")
)
async def cb_broadcast_cancel_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(texts.CANCELLED)
    await callback.message.answer(texts.ADMIN_MENU, reply_markup=admin_kb.admin_menu())
    await callback.answer()


@router.callback_query(
    Broadcast.waiting_for_confirm, BroadcastCB.filter(F.action == "send")
)
async def cb_broadcast_send(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    users_repo: UsersRepo,
) -> None:
    data = await state.get_data()
    recipients: list[int] = data["recipients"]
    source_chat_id: int = data["source_chat_id"]
    source_message_id: int = data["source_message_id"]
    buttons: list[list[str]] = data.get("buttons", [])
    admin_chat_id = callback.from_user.id

    await state.clear()
    await callback.message.edit_text(texts.BROADCAST_STARTED)
    await callback.answer()

    reply_markup = _build_url_markup(buttons)

    asyncio.create_task(
        _run_and_report(
            bot=bot,
            users_repo=users_repo,
            recipients=recipients,
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
            reply_markup=reply_markup,
            report_to=admin_chat_id,
        )
    )


def _build_url_markup(buttons: list[list[str]]) -> InlineKeyboardMarkup | None:
    if not buttons:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, url=url)] for text, url in buttons
        ]
    )


async def _run_and_report(
    *,
    bot: Bot,
    users_repo: UsersRepo,
    recipients: list[int],
    source_chat_id: int,
    source_message_id: int,
    reply_markup: InlineKeyboardMarkup | None,
    report_to: int,
) -> None:
    log.info("broadcast starting: recipients=%d", len(recipients))
    try:
        result = await broadcast_service.broadcast(
            bot=bot,
            users_repo=users_repo,
            recipients=recipients,
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
            reply_markup=reply_markup,
        )
        await bot.send_message(
            report_to,
            texts.BROADCAST_REPORT.format(
                sent=result.sent,
                blocked=result.blocked,
                errors=result.errors,
            ),
        )
    except Exception:
        log.exception("broadcast task failed")
        try:
            await bot.send_message(report_to, "⚠️ Рассылка прервана из-за ошибки. См. логи.")
        except Exception:
            log.exception("failed to send error report to admin")
