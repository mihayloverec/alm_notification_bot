from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import texts
from bot.keyboards.callbacks import (
    AddTournamentCB,
    AdminCB,
    BroadcastBtnCB,
    BroadcastCB,
    InquiryAdminCB,
    MenuBtnCB,
    MenuCB,
    OrganizerCB,
    PlayerCB,
    PlayersCB,
    TournamentCB,
)
from bot.repositories import MenuButton, Tournament, User


def admin_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_ADMIN_ADD, callback_data=AdminCB(action="add"))
    kb.button(text=texts.BTN_ADMIN_MANAGE, callback_data=AdminCB(action="manage"))
    kb.button(text=texts.BTN_ADMIN_BROADCAST, callback_data=AdminCB(action="broadcast"))
    kb.button(text=texts.BTN_ADMIN_PLAYERS, callback_data=AdminCB(action="players"))
    kb.button(text=texts.BTN_ADMIN_INQUIRY, callback_data=AdminCB(action="inquiry"))
    kb.button(text=texts.BTN_ADMIN_ORGANIZERS, callback_data=AdminCB(action="organizers"))
    kb.button(text=texts.BTN_ADMIN_MENU_BUTTONS, callback_data=AdminCB(action="menu_buttons"))
    kb.button(text=texts.BACK, callback_data=MenuCB(action="main"))
    kb.adjust(1)
    return kb.as_markup()


def organizer_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
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


def broadcast_confirm(buttons_count: int = 0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_BROADCAST_ADD_BUTTON, callback_data=BroadcastBtnCB(action="add"))
    if buttons_count > 0:
        kb.button(
            text=texts.BTN_BROADCAST_RESET_BUTTONS,
            callback_data=BroadcastBtnCB(action="reset"),
        )
    kb.button(text=texts.BTN_SEND, callback_data=BroadcastCB(action="send"))
    kb.button(text=texts.CANCEL, callback_data=BroadcastCB(action="cancel"))
    # add (row1), reset (row2 if any), send+cancel (row3)
    if buttons_count > 0:
        kb.adjust(1, 1, 2)
    else:
        kb.adjust(1, 2)
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


def player_card(u: User, *, is_admin: bool = True) -> InlineKeyboardMarkup:
    """Player card. Organizers see only Back; admins see ban/sub management."""
    kb = InlineKeyboardBuilder()
    if is_admin:
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


# ---------- Получатели обращений ----------

def inquiry_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=texts.BTN_INQUIRY_ADMIN_SK,
        callback_data=InquiryAdminCB(action="list", type="sk"),
    )
    kb.button(
        text=texts.BTN_INQUIRY_ADMIN_DK,
        callback_data=InquiryAdminCB(action="list", type="dk"),
    )
    kb.button(text=texts.BACK, callback_data=MenuCB(action="admin"))
    kb.adjust(2, 1)
    return kb.as_markup()


def inquiry_recipients_list(
    inquiry_type: str,
    users: list[User],
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for u in users:
        kb.button(
            text=_player_label(u),
            callback_data=InquiryAdminCB(
                action="del", type=inquiry_type, user_id=u.user_id
            ),
        )
    kb.button(
        text=texts.BTN_INQUIRY_ADD,
        callback_data=InquiryAdminCB(action="add", type=inquiry_type, page=0),
    )
    kb.button(
        text=texts.BACK,
        callback_data=InquiryAdminCB(action="menu"),
    )
    kb.adjust(1)
    return kb.as_markup()


def inquiry_pick_list(
    inquiry_type: str,
    users: list[User],
    *,
    page: int,
    pages: int,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for u in users:
        kb.button(
            text=_player_label(u),
            callback_data=InquiryAdminCB(
                action="pick", type=inquiry_type, user_id=u.user_id, page=page
            ),
        )
    kb.adjust(1)

    nav = InlineKeyboardBuilder()
    if pages > 1:
        if page > 0:
            nav.button(
                text=texts.BTN_PREV_PAGE,
                callback_data=InquiryAdminCB(
                    action="page", type=inquiry_type, page=page - 1
                ),
            )
        if page < pages - 1:
            nav.button(
                text=texts.BTN_NEXT_PAGE,
                callback_data=InquiryAdminCB(
                    action="page", type=inquiry_type, page=page + 1
                ),
            )
    nav.button(
        text=texts.BACK,
        callback_data=InquiryAdminCB(action="list", type=inquiry_type),
    )
    nav.adjust(2 if pages > 1 else 1, 1)
    kb.attach(nav)
    return kb.as_markup()


def inquiry_remove_confirm(inquiry_type: str, user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=texts.BTN_YES,
        callback_data=InquiryAdminCB(
            action="del_yes", type=inquiry_type, user_id=user_id
        ),
    )
    kb.button(
        text=texts.BTN_NO,
        callback_data=InquiryAdminCB(action="list", type=inquiry_type),
    )
    kb.adjust(2)
    return kb.as_markup()


# ---------- Организаторы ----------

def organizers_list(users: list[User]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for u in users:
        kb.button(
            text=_player_label(u),
            callback_data=OrganizerCB(action="del", user_id=u.user_id),
        )
    kb.button(
        text=texts.BTN_ORGANIZER_ADD,
        callback_data=OrganizerCB(action="add", page=0),
    )
    kb.button(text=texts.BACK, callback_data=MenuCB(action="admin"))
    kb.adjust(1)
    return kb.as_markup()


def organizer_pick_list(
    users: list[User],
    *,
    page: int,
    pages: int,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for u in users:
        kb.button(
            text=_player_label(u),
            callback_data=OrganizerCB(action="pick", user_id=u.user_id, page=page),
        )
    kb.adjust(1)

    nav = InlineKeyboardBuilder()
    if pages > 1:
        if page > 0:
            nav.button(
                text=texts.BTN_PREV_PAGE,
                callback_data=OrganizerCB(action="page", page=page - 1),
            )
        if page < pages - 1:
            nav.button(
                text=texts.BTN_NEXT_PAGE,
                callback_data=OrganizerCB(action="page", page=page + 1),
            )
    nav.button(
        text=texts.BTN_ORGANIZER_SEARCH,
        callback_data=OrganizerCB(action="search"),
    )
    nav.button(text=texts.BACK, callback_data=OrganizerCB(action="list"))
    nav.adjust(2 if pages > 1 else 1, 1, 1)
    kb.attach(nav)
    return kb.as_markup()


def organizer_search_results(users: list[User]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for u in users:
        kb.button(
            text=_player_label(u),
            callback_data=OrganizerCB(action="pick", user_id=u.user_id),
        )
    kb.button(
        text=texts.BTN_ORGANIZER_SEARCH,
        callback_data=OrganizerCB(action="search"),
    )
    kb.button(text=texts.BACK, callback_data=OrganizerCB(action="list"))
    kb.adjust(1)
    return kb.as_markup()


def organizer_remove_confirm(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=texts.BTN_YES,
        callback_data=OrganizerCB(action="del_yes", user_id=user_id),
    )
    kb.button(
        text=texts.BTN_NO,
        callback_data=OrganizerCB(action="list"),
    )
    kb.adjust(2)
    return kb.as_markup()


# ---------- Кастомные кнопки меню ----------

def menu_buttons_list(buttons: list[MenuButton]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for b in buttons:
        kb.button(
            text=b.text,
            callback_data=MenuBtnCB(action="view", button_id=b.id),
        )
    kb.button(
        text=texts.BTN_MENU_BUTTON_ADD,
        callback_data=MenuBtnCB(action="add"),
    )
    kb.button(text=texts.BACK, callback_data=MenuCB(action="admin"))
    kb.adjust(1)
    return kb.as_markup()


def menu_button_card(b: MenuButton, *, is_first: bool, is_last: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=texts.BTN_MENU_BUTTON_EDIT_TEXT,
        callback_data=MenuBtnCB(action="edit_text", button_id=b.id),
    )
    kb.button(
        text=texts.BTN_MENU_BUTTON_EDIT_URL,
        callback_data=MenuBtnCB(action="edit_url", button_id=b.id),
    )
    if not is_first:
        kb.button(
            text=texts.BTN_MENU_BUTTON_UP,
            callback_data=MenuBtnCB(action="up", button_id=b.id),
        )
    if not is_last:
        kb.button(
            text=texts.BTN_MENU_BUTTON_DOWN,
            callback_data=MenuBtnCB(action="down", button_id=b.id),
        )
    kb.button(
        text=texts.BTN_MENU_BUTTON_DELETE,
        callback_data=MenuBtnCB(action="del", button_id=b.id),
    )
    kb.button(text=texts.BACK, callback_data=MenuBtnCB(action="list"))

    # edit text/url one row; up/down one row (2 buttons if both available, 1 otherwise);
    # delete; back
    second_row = sum(1 for x in (not is_first, not is_last) if x)
    rows = [2]
    if second_row > 0:
        rows.append(second_row)
    rows.extend([1, 1])
    kb.adjust(*rows)
    return kb.as_markup()


def menu_button_delete_confirm(button_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=texts.BTN_YES,
        callback_data=MenuBtnCB(action="del_yes", button_id=button_id),
    )
    kb.button(
        text=texts.BTN_NO,
        callback_data=MenuBtnCB(action="view", button_id=button_id),
    )
    kb.adjust(2)
    return kb.as_markup()
