from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import texts
from bot.keyboards import user as user_kb
from bot.keyboards.callbacks import MenuCB, TournamentCB
from bot.repositories import SubscriptionsRepo, TournamentsRepo

router = Router(name="user")


@router.callback_query(MenuCB.filter(F.action == "tournaments"))
async def cb_tournaments(
    callback: CallbackQuery,
    tournaments_repo: TournamentsRepo,
) -> None:
    tournaments = await tournaments_repo.list_active()
    if not tournaments:
        await callback.message.edit_text(
            texts.NO_ACTIVE_TOURNAMENTS,
            reply_markup=user_kb.empty_back(),
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        "Активные турниры:",
        reply_markup=user_kb.tournaments_list(tournaments),
    )
    await callback.answer()


@router.callback_query(MenuCB.filter(F.action == "my_subs"))
async def cb_my_subs(
    callback: CallbackQuery,
    tournaments_repo: TournamentsRepo,
    subscriptions_repo: SubscriptionsRepo,
) -> None:
    ids = await subscriptions_repo.list_user_tournament_ids(callback.from_user.id)
    if not ids:
        await callback.message.edit_text(
            texts.NO_SUBSCRIPTIONS,
            reply_markup=user_kb.empty_back(),
        )
        await callback.answer()
        return
    tournaments = []
    for tid in ids:
        t = await tournaments_repo.get(tid)
        if t is not None:
            tournaments.append(t)
    await callback.message.edit_text(
        "Твои подписки:",
        reply_markup=user_kb.tournaments_list(tournaments, show_closed_marker=True),
    )
    await callback.answer()


@router.callback_query(TournamentCB.filter(F.action == "view"))
async def cb_view_tournament(
    callback: CallbackQuery,
    callback_data: TournamentCB,
    tournaments_repo: TournamentsRepo,
    subscriptions_repo: SubscriptionsRepo,
) -> None:
    t = await tournaments_repo.get(callback_data.tournament_id)
    if t is None:
        await callback.answer("Турнир не найден", show_alert=True)
        return
    is_sub = await subscriptions_repo.is_subscribed(
        callback.from_user.id, callback_data.tournament_id
    )
    text = texts.render_card(t.name, t.description, closed=not t.is_active)
    back_to = "my_subs" if not t.is_active else "tournaments"
    await callback.message.edit_text(
        text,
        reply_markup=user_kb.tournament_card(t.id, is_sub, back_to=back_to),
    )
    await callback.answer()


@router.callback_query(TournamentCB.filter(F.action == "sub"))
async def cb_subscribe(
    callback: CallbackQuery,
    callback_data: TournamentCB,
    tournaments_repo: TournamentsRepo,
    subscriptions_repo: SubscriptionsRepo,
) -> None:
    t = await tournaments_repo.get(callback_data.tournament_id)
    if t is None or not t.is_active:
        await callback.answer("Турнир недоступен", show_alert=True)
        return
    await subscriptions_repo.subscribe(callback.from_user.id, t.id)
    await callback.answer(texts.SUBSCRIBED)
    await callback.message.edit_reply_markup(
        reply_markup=user_kb.tournament_card(t.id, is_subscribed=True)
    )


@router.callback_query(TournamentCB.filter(F.action == "unsub"))
async def cb_unsubscribe(
    callback: CallbackQuery,
    callback_data: TournamentCB,
    tournaments_repo: TournamentsRepo,
    subscriptions_repo: SubscriptionsRepo,
) -> None:
    t = await tournaments_repo.get(callback_data.tournament_id)
    if t is None:
        await callback.answer("Турнир не найден", show_alert=True)
        return
    await subscriptions_repo.unsubscribe(callback.from_user.id, t.id)
    await callback.answer(texts.UNSUBSCRIBED)
    back_to = "my_subs" if not t.is_active else "tournaments"
    await callback.message.edit_reply_markup(
        reply_markup=user_kb.tournament_card(t.id, is_subscribed=False, back_to=back_to)
    )
