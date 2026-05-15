from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import texts
from bot.keyboards.callbacks import (
    AddTournamentCB,
    AdminCB,
    BroadcastCB,
    MenuCB,
    TournamentCB,
)
from bot.repositories import Tournament


def admin_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_ADMIN_ADD, callback_data=AdminCB(action="add"))
    kb.button(text=texts.BTN_ADMIN_MANAGE, callback_data=AdminCB(action="manage"))
    kb.button(text=texts.BTN_ADMIN_BROADCAST, callback_data=AdminCB(action="broadcast"))
    kb.button(text=texts.BACK, callback_data=MenuCB(action="main"))
    kb.adjust(1)
    return kb.as_markup()


def add_tournament_confirm() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_SAVE, callback_data=AddTournamentCB(action="save"))
    kb.button(text=texts.CANCEL, callback_data=AddTournamentCB(action="cancel"))
    kb.adjust(2)
    return kb.as_markup()


def manage_list(tournaments: list[Tournament]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for t in tournaments:
        marker = "🟢" if t.is_active else "🔴"
        kb.button(
            text=f"{marker} {t.name}",
            callback_data=TournamentCB(action="manage", tournament_id=t.id),
        )
    kb.button(text=texts.BACK, callback_data=MenuCB(action="admin"))
    kb.adjust(1)
    return kb.as_markup()


def manage_card(tournament: Tournament) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=texts.BTN_EDIT_NAME,
        callback_data=TournamentCB(action="edit_name", tournament_id=tournament.id),
    )
    kb.button(
        text=texts.BTN_EDIT_DESCRIPTION,
        callback_data=TournamentCB(action="edit_desc", tournament_id=tournament.id),
    )
    toggle_text = texts.BTN_CLOSE if tournament.is_active else texts.BTN_OPEN
    kb.button(
        text=toggle_text,
        callback_data=TournamentCB(action="toggle", tournament_id=tournament.id),
    )
    kb.button(text=texts.BACK, callback_data=AdminCB(action="manage"))
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def broadcast_audience(tournaments: list[Tournament]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_AUDIENCE_ALL, callback_data=BroadcastCB(action="all"))
    for t in tournaments:
        kb.button(
            text=f"📋 {t.name}",
            callback_data=BroadcastCB(action="tournament", tournament_id=t.id),
        )
    kb.button(text=texts.CANCEL, callback_data=BroadcastCB(action="cancel"))
    kb.adjust(1)
    return kb.as_markup()


def broadcast_confirm() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_SEND, callback_data=BroadcastCB(action="send"))
    kb.button(text=texts.CANCEL, callback_data=BroadcastCB(action="cancel"))
    kb.adjust(2)
    return kb.as_markup()
