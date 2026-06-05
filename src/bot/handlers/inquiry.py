from __future__ import annotations

import html
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.keyboards import user as user_kb
from bot.keyboards.callbacks import InquiryUserCB
from bot.repositories import INQUIRY_TYPES, InquiryRecipientsRepo, UsersRepo
from bot.states import Inquiry

log = logging.getLogger(__name__)

router = Router(name="inquiry")


@router.callback_query(InquiryUserCB.filter(F.action == "start"))
async def cb_inquiry_start(
    callback: CallbackQuery,
    callback_data: InquiryUserCB,
    state: FSMContext,
    inquiry_recipients_repo: InquiryRecipientsRepo,
) -> None:
    inquiry_type = callback_data.type
    if inquiry_type not in INQUIRY_TYPES:
        await callback.answer()
        return

    label = texts.INQUIRY_LABEL[inquiry_type]
    if not await inquiry_recipients_repo.has_any(inquiry_type):
        await callback.message.edit_text(
            texts.INQUIRY_UNAVAILABLE.format(label=label),
            reply_markup=user_kb.empty_back(),
        )
        await callback.answer()
        return

    await state.set_state(Inquiry.waiting_for_message)
    await state.update_data(type=inquiry_type)
    await callback.message.edit_text(texts.INQUIRY_ENTER_MESSAGE.format(label=label))
    await callback.answer()


@router.message(Inquiry.waiting_for_message)
async def msg_inquiry_received(
    message: Message,
    state: FSMContext,
    inquiry_recipients_repo: InquiryRecipientsRepo,
) -> None:
    data = await state.get_data()
    inquiry_type: str = data.get("type", "")
    if inquiry_type not in INQUIRY_TYPES:
        await state.clear()
        return

    label = texts.INQUIRY_LABEL[inquiry_type]
    recipients = await inquiry_recipients_repo.list_active_recipient_ids(inquiry_type)
    if not recipients:
        await state.clear()
        await message.answer(texts.INQUIRY_UNAVAILABLE.format(label=label))
        return

    await state.set_state(Inquiry.waiting_for_confirm)
    await state.update_data(
        source_chat_id=message.chat.id,
        source_message_id=message.message_id,
    )
    await message.answer(
        texts.INQUIRY_PREVIEW.format(count=len(recipients)),
        reply_markup=user_kb.inquiry_confirm(inquiry_type),
    )


@router.callback_query(
    Inquiry.waiting_for_confirm, InquiryUserCB.filter(F.action == "cancel")
)
async def cb_inquiry_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(texts.CANCELLED)
    await callback.answer()


@router.callback_query(
    Inquiry.waiting_for_confirm, InquiryUserCB.filter(F.action == "send")
)
async def cb_inquiry_send(
    callback: CallbackQuery,
    callback_data: InquiryUserCB,
    state: FSMContext,
    bot: Bot,
    inquiry_recipients_repo: InquiryRecipientsRepo,
    users_repo: UsersRepo,
) -> None:
    data = await state.get_data()
    inquiry_type = callback_data.type
    if inquiry_type not in INQUIRY_TYPES:
        await state.clear()
        await callback.answer()
        return

    source_chat_id: int = data["source_chat_id"]
    source_message_id: int = data["source_message_id"]
    await state.clear()

    label = texts.INQUIRY_LABEL[inquiry_type]
    recipients = await inquiry_recipients_repo.list_active_recipient_ids(inquiry_type)

    if not recipients:
        await callback.message.edit_text(texts.INQUIRY_UNAVAILABLE.format(label=label))
        await callback.answer()
        return

    sender = callback.from_user
    username_line = (
        f"@{html.escape(sender.username)}\n" if sender.username else "—\n"
    )
    header = texts.INQUIRY_HEADER.format(
        label=label,
        username_line=username_line,
        user_id=sender.id,
        first_name=html.escape(sender.first_name or "—"),
    )

    delivered = 0
    for recipient_id in recipients:
        ok = await _send_to(
            bot, recipient_id, header, source_chat_id, source_message_id, users_repo
        )
        if ok:
            delivered += 1

    if delivered == 0:
        await callback.message.edit_text(texts.INQUIRY_SEND_FAILED)
    else:
        await callback.message.edit_text(texts.INQUIRY_SENT.format(label=label))
    await callback.answer()


async def _send_to(
    bot: Bot,
    recipient_id: int,
    header: str,
    source_chat_id: int,
    source_message_id: int,
    users_repo: UsersRepo,
) -> bool:
    try:
        await bot.send_message(recipient_id, header)
        await bot.copy_message(
            chat_id=recipient_id,
            from_chat_id=source_chat_id,
            message_id=source_message_id,
        )
        return True
    except TelegramForbiddenError:
        await users_repo.mark_blocked(recipient_id)
        return False
    except TelegramBadRequest as e:
        msg = (e.message or "").lower()
        if "chat not found" in msg or "user is deactivated" in msg or "blocked" in msg:
            await users_repo.mark_blocked(recipient_id)
        else:
            log.exception("inquiry: bad request for recipient_id=%s", recipient_id)
        return False
    except Exception:
        log.exception("inquiry: unexpected error for recipient_id=%s", recipient_id)
        return False
