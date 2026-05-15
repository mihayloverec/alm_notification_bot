from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import texts
from bot.keyboards.callbacks import MenuCB, TournamentCB
from bot.repositories import Tournament


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_TOURNAMENTS, callback_data=MenuCB(action="tournaments"))
    kb.button(text=texts.BTN_MY_SUBS, callback_data=MenuCB(action="my_subs"))
    if is_admin:
        kb.button(text="🛠 Админ", callback_data=MenuCB(action="admin"))
    kb.adjust(2, 1)
    return kb.as_markup()


def tournaments_list(
    tournaments: list[Tournament],
    *,
    show_closed_marker: bool = False,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for t in tournaments:
        label = t.name if t.is_active or not show_closed_marker else f"{t.name} [Закрыт]"
        kb.button(
            text=label,
            callback_data=TournamentCB(action="view", tournament_id=t.id),
        )
    kb.button(text=texts.BACK, callback_data=MenuCB(action="main"))
    kb.adjust(1)
    return kb.as_markup()


def tournament_card(
    tournament_id: int,
    is_subscribed: bool,
    *,
    back_to: str = "tournaments",
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if is_subscribed:
        kb.button(
            text=texts.BTN_UNSUBSCRIBE,
            callback_data=TournamentCB(action="unsub", tournament_id=tournament_id),
        )
    else:
        kb.button(
            text=texts.BTN_SUBSCRIBE,
            callback_data=TournamentCB(action="sub", tournament_id=tournament_id),
        )
    kb.button(text=texts.BACK, callback_data=MenuCB(action=back_to))
    kb.adjust(1)
    return kb.as_markup()


def empty_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.BACK, callback_data=MenuCB(action="main").pack())]
        ]
    )
