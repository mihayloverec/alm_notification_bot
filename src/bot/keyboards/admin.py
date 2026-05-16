from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import texts
from bot.keyboards.callbacks import (
    AddTournamentCB,
    AdminCB,
    BroadcastCB,
    MenuCB,
    PlayerCB,
    PlayersCB,
    TournamentCB,
)
from bot.repositories import Tournament, User


def admin_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_ADMIN_ADD, callback_data=AdminCB(action="add"))
    kb.button(text=texts.BTN_ADMIN_MANAGE, callback_data=AdminCB(action="manage"))
    kb.button(text=texts.BTN_ADMIN_BROADCAST, callback_data=AdminCB(action="broadcast"))
    kb.button(text=texts.BTN_ADMIN_PLAYERS, callback_data=AdminCB(action="players"))
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


def _player_label(u: User) -> str:
    base = (
        f"@{u.username}"
        if u.username
        else (u.first_name or f"id:{u.user_id}")
    )
    marker = " 🚫" if u.is_banned else ""
    return f"{base}{marker}"


def players_list(
    users: list[User],
    *,
    page: int,
    pages: int,
    show_pagination: bool,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for u in users:
        kb.button(
            text=_player_label(u),
            callback_data=PlayerCB(action="view", user_id=u.user_id),
        )
    kb.adjust(1)

    nav = InlineKeyboardBuilder()
    if show_pagination and pages > 1:
        if page > 0:
            nav.button(
                text=texts.BTN_PREV_PAGE,
                callback_data=PlayersCB(action="page", page=page - 1),
            )
        if page < pages - 1:
            nav.button(
                text=texts.BTN_NEXT_PAGE,
                callback_data=PlayersCB(action="page", page=page + 1),
            )
    nav.button(text=texts.BTN_SEARCH, callback_data=PlayersCB(action="search"))
    nav.button(text=texts.BACK, callback_data=MenuCB(action="admin"))
    nav.adjust(2 if (show_pagination and pages > 1) else 1, 2)
    kb.attach(nav)
    return kb.as_markup()


def search_results(users: list[User]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for u in users:
        kb.button(
            text=_player_label(u),
            callback_data=PlayerCB(action="view", user_id=u.user_id),
        )
    kb.button(text=texts.BTN_SEARCH, callback_data=PlayersCB(action="search"))
    kb.button(text=texts.BACK, callback_data=PlayersCB(action="list", page=0))
    kb.adjust(1)
    return kb.as_markup()


def player_card(u: User) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=texts.BTN_UNBAN if u.is_banned else texts.BTN_BAN,
        callback_data=PlayerCB(
            action="unban" if u.is_banned else "ban",
            user_id=u.user_id,
        ),
    )
    kb.button(
        text=texts.BTN_PLAYER_ADD_SUB,
        callback_data=PlayerCB(action="sub_list", user_id=u.user_id),
    )
    kb.button(
        text=texts.BTN_PLAYER_SUBS,
        callback_data=PlayerCB(action="subs", user_id=u.user_id),
    )
    kb.button(text=texts.BACK, callback_data=PlayersCB(action="list", page=0))
    kb.adjust(1)
    return kb.as_markup()


def player_subscribe_list(
    user_id: int,
    tournaments: list[Tournament],
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for t in tournaments:
        kb.button(
            text=t.name,
            callback_data=PlayerCB(action="sub", user_id=user_id, tournament_id=t.id),
        )
    kb.button(
        text=texts.BACK,
        callback_data=PlayerCB(action="view", user_id=user_id),
    )
    kb.adjust(1)
    return kb.as_markup()


def player_subscriptions(
    user_id: int,
    tournaments: list[Tournament],
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for t in tournaments:
        suffix = "" if t.is_active else " [Закрыт]"
        kb.button(
            text=f"➖ {t.name}{suffix}",
            callback_data=PlayerCB(
                action="unsub", user_id=user_id, tournament_id=t.id
            ),
        )
    kb.button(
        text=texts.BACK,
        callback_data=PlayerCB(action="view", user_id=user_id),
    )
    kb.adjust(1)
    return kb.as_markup()
