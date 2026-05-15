from __future__ import annotations

from bot.services import broadcast as broadcast_service


async def test_recipients_all_excludes_blocked(users_repo):
    for uid in (10, 20, 30):
        await users_repo.upsert(uid, None, None)
    await users_repo.mark_blocked(20)

    recipients = await broadcast_service.get_recipients(users_repo, tournament_id=None)
    assert recipients == [10, 30]


async def test_recipients_per_tournament(
    users_repo, tournaments_repo, subscriptions_repo
):
    for uid in (1, 2, 3, 4):
        await users_repo.upsert(uid, None, None)
    t1 = await tournaments_repo.create("T1", "")
    t2 = await tournaments_repo.create("T2", "")

    # 1, 2 → t1; 3 → t2; 4 — без подписок
    await subscriptions_repo.subscribe(1, t1)
    await subscriptions_repo.subscribe(2, t1)
    await subscriptions_repo.subscribe(3, t2)

    # user 1 заблокировал бота
    await users_repo.mark_blocked(1)

    r1 = await broadcast_service.get_recipients(users_repo, tournament_id=t1)
    r2 = await broadcast_service.get_recipients(users_repo, tournament_id=t2)
    r_all = await broadcast_service.get_recipients(users_repo, tournament_id=None)

    assert r1 == [2]            # 1 заблокирован, 2 подписан
    assert r2 == [3]
    assert r_all == [2, 3, 4]   # 1 заблокирован, остальные активны
