from __future__ import annotations

import html
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import texts
from bot.config import Config
from bot.keyboards import user as user_kb
from bot.keyboards.callbacks import InquiryBanCB, InquiryReplyCB, InquiryUserCB
from bot.repositories import INQUIRY_TYPES, InquiryRecipientsRepo, UsersRepo
from bot.states import Inquiry, InquiryReply

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
        await message.answer(
            texts.INQUIRY_UNAVAILABLE.format(label=label),
            reply_markup=user_kb.to_main_menu(),
        )
        return

    await state.set_state(Inquiry.waiting_for_confirm)
    await state.update_data(
        source_chat_id=message.chat.id,
        source_message_id=message.message_id,
    )
    await message.answer(
        texts.INQUIRY_PREVIEW,
        reply_markup=user_kb.inquiry_confirm(inquiry_type),
    )


@router.callback_query(
    Inquiry.waiting_for_confirm, InquiryUserCB.filter(F.action == "cancel")
)
async def cb_inquiry_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        texts.CANCELLED, reply_markup=user_kb.to_main_menu()
    )
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

    actions_kb = _recipient_actions_kb(sender.id, inquiry_type)

    delivered = 0
    for recipient_id in recipients:
        ok = await _send_to(
            bot,
            recipient_id,
            header,
            source_chat_id,
            source_message_id,
            users_repo,
            actions_kb=actions_kb,
        )
        if ok:
            delivered += 1

    if delivered == 0:
        await callback.message.edit_text(
            texts.INQUIRY_SEND_FAILED, reply_markup=user_kb.to_main_menu()
        )
    else:
        await callback.message.edit_text(
            texts.INQUIRY_SENT.format(label=label),
            reply_markup=user_kb.to_main_menu(),
        )
    await callback.answer()


async def _send_to(
    bot: Bot,
    recipient_id: int,
    header: str,
    source_chat_id: int,
    source_message_id: int,
    users_repo: UsersRepo,
    *,
    actions_kb: InlineKeyboardMarkup | None = None,
) -> bool:
    try:
        await bot.send_message(recipient_id, header, reply_markup=actions_kb)
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


def _recipient_actions_kb(sender_id: int, inquiry_type: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=texts.INQUIRY_RECIPIENT_BTN_REPLY,
        callback_data=InquiryReplyCB(sender_id=sender_id, type=inquiry_type),
    )
    kb.button(
        text=texts.INQUIRY_RECIPIENT_BTN_BAN,
        callback_data=InquiryBanCB(action="init", sender_id=sender_id),
    )
    kb.adjust(2)
    return kb.as_markup()


def _ban_confirm_kb(sender_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=texts.BTN_YES,
        callback_data=InquiryBanCB(action="yes", sender_id=sender_id),
    )
    kb.button(
        text=texts.BTN_NO,
        callback_data=InquiryBanCB(action="no", sender_id=sender_id),
    )
    kb.adjust(2)
    return kb.as_markup()


async def _can_act_on_inquiry(
    user_id: int,
    config: Config,
    inquiry_recipients_repo: InquiryRecipientsRepo,
) -> bool:
    if config.is_admin(user_id):
        return True
    return await inquiry_recipients_repo.is_recipient_anywhere(user_id)


# ---------- Ответ получателя ----------

@router.callback_query(InquiryReplyCB.filter())
async def cb_inquiry_reply_start(
    callback: CallbackQuery,
    callback_data: InquiryReplyCB,
    state: FSMContext,
    config: Config,
    inquiry_recipients_repo: InquiryRecipientsRepo,
) -> None:
    if not await _can_act_on_inquiry(
        callback.from_user.id, config, inquiry_recipients_repo
    ):
        await callback.answer(texts.INQUIRY_ACTION_NOT_AUTHORIZED, show_alert=True)
        return
    await state.set_state(InquiryReply.waiting_for_message)
    await state.update_data(
        sender_id=callback_data.sender_id,
        type=callback_data.type,
    )
    await callback.message.answer(texts.INQUIRY_REPLY_PROMPT)
    await callback.answer()


@router.message(InquiryReply.waiting_for_message)
async def msg_inquiry_reply_received(
    message: Message,
    state: FSMContext,
    bot: Bot,
    users_repo: UsersRepo,
) -> None:
    data = await state.get_data()
    sender_id: int = data["sender_id"]
    inquiry_type: str = data.get("type", "")
    await state.clear()

    label = texts.INQUIRY_LABEL.get(inquiry_type, inquiry_type)
    try:
        await bot.send_message(
            sender_id, texts.INQUIRY_REPLY_HEADER.format(label=label)
        )
        await bot.copy_message(
            chat_id=sender_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
        await message.answer(
            texts.INQUIRY_REPLY_SENT, reply_markup=user_kb.to_main_menu()
        )
    except TelegramForbiddenError:
        await users_repo.mark_blocked(sender_id)
        await message.answer(
            texts.INQUIRY_REPLY_FAILED, reply_markup=user_kb.to_main_menu()
        )
    except Exception:
        log.exception("inquiry reply: failed for sender_id=%s", sender_id)
        await message.answer(
            texts.INQUIRY_REPLY_FAILED, reply_markup=user_kb.to_main_menu()
        )


# ---------- Бан получателем ----------

@router.callback_query(InquiryBanCB.filter(F.action == "init"))
async def cb_inquiry_ban_init(
    callback: CallbackQuery,
    callback_data: InquiryBanCB,
    config: Config,
    inquiry_recipients_repo: InquiryRecipientsRepo,
) -> None:
    if not await _can_act_on_inquiry(
        callback.from_user.id, config, inquiry_recipients_repo
    ):
        await callback.answer(texts.INQUIRY_ACTION_NOT_AUTHORIZED, show_alert=True)
        return
    if callback_data.sender_id == callback.from_user.id:
        await callback.answer(texts.INQUIRY_BAN_SELF_FORBIDDEN, show_alert=True)
        return
    if config.is_admin(callback_data.sender_id):
        await callback.answer(texts.INQUIRY_BAN_ADMIN_FORBIDDEN, show_alert=True)
        return
    # Отдельным сообщением, оригинал с обращением не трогаем
    await callback.message.answer(
        texts.INQUIRY_BAN_CONFIRM,
        reply_markup=_ban_confirm_kb(callback_data.sender_id),
    )
    await callback.answer()


@router.callback_query(InquiryBanCB.filter(F.action == "yes"))
async def cb_inquiry_ban_yes(
    callback: CallbackQuery,
    callback_data: InquiryBanCB,
    config: Config,
    inquiry_recipients_repo: InquiryRecipientsRepo,
    users_repo: UsersRepo,
) -> None:
    if not await _can_act_on_inquiry(
        callback.from_user.id, config, inquiry_recipients_repo
    ):
        await callback.answer(texts.INQUIRY_ACTION_NOT_AUTHORIZED, show_alert=True)
        return
    if config.is_admin(callback_data.sender_id):
        await callback.answer(texts.INQUIRY_BAN_ADMIN_FORBIDDEN, show_alert=True)
        return
    await users_repo.set_banned(callback_data.sender_id, True)
    await callback.message.edit_text(texts.INQUIRY_BAN_DONE)
    await callback.answer()


@router.callback_query(InquiryBanCB.filter(F.action == "no"))
async def cb_inquiry_ban_no(callback: CallbackQuery) -> None:
    await callback.message.edit_text(texts.INQUIRY_BAN_CANCELLED)
    await callback.answer()
