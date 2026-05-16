from __future__ import annotations

import html
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.config import Config
from bot.keyboards import admin as admin_kb
from bot.keyboards.callbacks import AdminCB, PlayerCB, PlayersCB
from bot.middlewares.admin_only import AdminOnlyMiddleware
from bot.repositories import (
    SubscriptionsRepo,
    TournamentsRepo,
    User,
    UsersRepo,
)
from bot.states import SearchPlayers

router = Router(name="admin_players")
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())

PAGE_SIZE = 10


# ---------- список игроков ----------

@router.callback_query(AdminCB.filter(F.action == "players"))
async def cb_players_entry(
    callback: CallbackQuery,
    state: FSMContext,
    users_repo: UsersRepo,
) -> None:
    await state.clear()
    await _show_players_page(callback, users_repo, page=0)


@router.callback_query(PlayersCB.filter(F.action == "list"))
async def cb_players_list(
    callback: CallbackQuery,
    state: FSMContext,
    users_repo: UsersRepo,
) -> None:
    await state.clear()
    await _show_players_page(callback, users_repo, page=0)


@router.callback_query(PlayersCB.filter(F.action == "page"))
async def cb_players_page(
    callback: CallbackQuery,
    callback_data: PlayersCB,
    users_repo: UsersRepo,
) -> None:
    await _show_players_page(callback, users_repo, page=callback_data.page)


async def _show_players_page(
    callback: CallbackQuery,
    users_repo: UsersRepo,
    *,
    page: int,
) -> None:
    total = await users_repo.count()
    if total == 0:
        await callback.message.edit_text(
            texts.PLAYERS_LIST_EMPTY,
            reply_markup=admin_kb.players_list(
                [], page=0, pages=1, show_pagination=False
            ),
        )
        await callback.answer()
        return

    pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(0, min(page, pages - 1))
    users = await users_repo.list_page(offset=page * PAGE_SIZE, limit=PAGE_SIZE)

    await callback.message.edit_text(
        texts.PLAYERS_LIST_HEADER.format(total=total, page=page + 1, pages=pages),
        reply_markup=admin_kb.players_list(
            users, page=page, pages=pages, show_pagination=True
        ),
    )
    await callback.answer()


# ---------- поиск ----------

@router.callback_query(PlayersCB.filter(F.action == "search"))
async def cb_search_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SearchPlayers.waiting_for_query)
    await callback.message.edit_text(texts.SEARCH_ENTER_QUERY)
    await callback.answer()


@router.message(SearchPlayers.waiting_for_query)
async def msg_search_query(
    message: Message,
    state: FSMContext,
    users_repo: UsersRepo,
) -> None:
    q = (message.text or "").strip()
    await state.clear()
    if not q:
        await message.answer(texts.SEARCH_NO_RESULTS.format(q=""))
        return
    results = await users_repo.search(q)
    if not results:
        await message.answer(
            texts.SEARCH_NO_RESULTS.format(q=html.escape(q)),
            reply_markup=admin_kb.search_results([]),
        )
        return
    await message.answer(
        texts.SEARCH_RESULTS_HEADER.format(n=len(results)),
        reply_markup=admin_kb.search_results(results),
    )


# ---------- карточка игрока ----------

@router.callback_query(PlayerCB.filter(F.action == "view"))
async def cb_player_view(
    callback: CallbackQuery,
    callback_data: PlayerCB,
    users_repo: UsersRepo,
    subscriptions_repo: SubscriptionsRepo,
) -> None:
    u = await users_repo.get(callback_data.user_id)
    if u is None:
        await callback.answer("Игрок не найден", show_alert=True)
        return
    subs_count = await subscriptions_repo.count_for_user(u.user_id)
    await callback.message.edit_text(
        _render_player_card(u, subs_count),
        reply_markup=admin_kb.player_card(u),
    )
    await callback.answer()


# ---------- бан / разбан ----------

@router.callback_query(PlayerCB.filter(F.action == "ban"))
async def cb_player_ban(
    callback: CallbackQuery,
    callback_data: PlayerCB,
    users_repo: UsersRepo,
    subscriptions_repo: SubscriptionsRepo,
    config: Config,
) -> None:
    if callback_data.user_id == callback.from_user.id or config.is_admin(
        callback_data.user_id
    ):
        await callback.answer(texts.PLAYER_SELF_BAN_FORBIDDEN, show_alert=True)
        return
    await users_repo.set_banned(callback_data.user_id, True)
    await callback.answer(texts.PLAYER_BANNED)
    await _refresh_player_card(callback, callback_data.user_id, users_repo, subscriptions_repo)


@router.callback_query(PlayerCB.filter(F.action == "unban"))
async def cb_player_unban(
    callback: CallbackQuery,
    callback_data: PlayerCB,
    users_repo: UsersRepo,
    subscriptions_repo: SubscriptionsRepo,
) -> None:
    await users_repo.set_banned(callback_data.user_id, False)
    await callback.answer(texts.PLAYER_UNBANNED)
    await _refresh_player_card(callback, callback_data.user_id, users_repo, subscriptions_repo)


# ---------- подписки игрока (управление от админа) ----------

@router.callback_query(PlayerCB.filter(F.action == "sub_list"))
async def cb_player_sub_list(
    callback: CallbackQuery,
    callback_data: PlayerCB,
    tournaments_repo: TournamentsRepo,
) -> None:
    active = await tournaments_repo.list_active()
    if not active:
        await callback.answer(texts.NO_ACTIVE_TOURNAMENTS_ADMIN, show_alert=True)
        return
    await callback.message.edit_text(
        texts.PLAYER_CHOOSE_TOURNAMENT,
        reply_markup=admin_kb.player_subscribe_list(callback_data.user_id, active),
    )
    await callback.answer()


@router.callback_query(PlayerCB.filter(F.action == "sub"))
async def cb_player_sub(
    callback: CallbackQuery,
    callback_data: PlayerCB,
    tournaments_repo: TournamentsRepo,
    subscriptions_repo: SubscriptionsRepo,
    users_repo: UsersRepo,
) -> None:
    t = await tournaments_repo.get(callback_data.tournament_id)
    if t is None:
        await callback.answer("Турнир не найден", show_alert=True)
        return
    await subscriptions_repo.subscribe(callback_data.user_id, t.id)
    await callback.answer(texts.PLAYER_SUBSCRIBED.format(name=t.name))
    await _refresh_player_card(callback, callback_data.user_id, users_repo, subscriptions_repo)


@router.callback_query(PlayerCB.filter(F.action == "subs"))
async def cb_player_subs(
    callback: CallbackQuery,
    callback_data: PlayerCB,
    subscriptions_repo: SubscriptionsRepo,
    tournaments_repo: TournamentsRepo,
) -> None:
    ids = await subscriptions_repo.list_user_tournament_ids(callback_data.user_id)
    if not ids:
        await callback.answer(texts.PLAYER_NO_SUBS, show_alert=True)
        return
    tournaments = []
    for tid in ids:
        t = await tournaments_repo.get(tid)
        if t is not None:
            tournaments.append(t)
    await callback.message.edit_text(
        texts.PLAYER_SUBS_LIST,
        reply_markup=admin_kb.player_subscriptions(callback_data.user_id, tournaments),
    )
    await callback.answer()


@router.callback_query(PlayerCB.filter(F.action == "unsub"))
async def cb_player_unsub(
    callback: CallbackQuery,
    callback_data: PlayerCB,
    tournaments_repo: TournamentsRepo,
    subscriptions_repo: SubscriptionsRepo,
    users_repo: UsersRepo,
) -> None:
    t = await tournaments_repo.get(callback_data.tournament_id)
    name = t.name if t else "—"
    await subscriptions_repo.unsubscribe(callback_data.user_id, callback_data.tournament_id)
    await callback.answer(texts.PLAYER_UNSUBSCRIBED.format(name=name))
    await _refresh_player_card(callback, callback_data.user_id, users_repo, subscriptions_repo)


# ---------- helpers ----------

async def _refresh_player_card(
    callback: CallbackQuery,
    user_id: int,
    users_repo: UsersRepo,
    subscriptions_repo: SubscriptionsRepo,
) -> None:
    u = await users_repo.get(user_id)
    if u is None:
        return
    subs_count = await subscriptions_repo.count_for_user(u.user_id)
    await callback.message.edit_text(
        _render_player_card(u, subs_count),
        reply_markup=admin_kb.player_card(u),
    )


def _render_player_card(u: User, subs: int) -> str:
    display = u.first_name or (f"@{u.username}" if u.username else f"id:{u.user_id}")
    username_line = (
        f"Username: @{html.escape(u.username)}\n" if u.username else ""
    )
    if u.is_banned:
        status = texts.PLAYER_STATUS_BANNED
    elif u.is_blocked:
        status = texts.PLAYER_STATUS_BLOCKED
    else:
        status = texts.PLAYER_STATUS_OK
    return texts.PLAYER_CARD.format(
        display_name=html.escape(display),
        user_id=u.user_id,
        username_line=username_line,
        created_at=u.created_at,
        status=status,
        subs=subs,
    )
