from __future__ import annotations

import pytest


async def test_create_and_get_tournament(tournaments_repo):
    tid = await tournaments_repo.create("Cup 1", "First cup")
    t = await tournaments_repo.get(tid)
    assert t is not None
    assert t.name == "Cup 1"
    assert t.description == "First cup"
    assert t.is_active is True


async def test_list_active_excludes_closed(tournaments_repo):
    a = await tournaments_repo.create("Active", "")
    b = await tournaments_repo.create("Closed", "")
    await tournaments_repo.set_active(b, False)

    active = await tournaments_repo.list_active()
    assert [t.id for t in active] == [a]

    all_ = await tournaments_repo.list_all()
    assert {t.id for t in all_} == {a, b}


async def test_edit_name_and_description(tournaments_repo):
    tid = await tournaments_repo.create("Old", "Old desc")
    await tournaments_repo.set_name(tid, "New")
    await tournaments_repo.set_description(tid, "New desc")
    t = await tournaments_repo.get(tid)
    assert t.name == "New"
    assert t.description == "New desc"


async def test_toggle_active(tournaments_repo):
    tid = await tournaments_repo.create("X", "")
    await tournaments_repo.set_active(tid, False)
    assert (await tournaments_repo.get(tid)).is_active is False
    await tournaments_repo.set_active(tid, True)
    assert (await tournaments_repo.get(tid)).is_active is True


async def test_user_upsert_and_get(users_repo):
    await users_repo.upsert(1, "alice", "Alice")
    u = await users_repo.get(1)
    assert u.user_id == 1
    assert u.username == "alice"
    assert u.first_name == "Alice"
    assert u.is_blocked is False

    # upsert resets is_blocked back to 0 (user came back)
    await users_repo.mark_blocked(1)
    assert (await users_repo.get(1)).is_blocked is True
    await users_repo.upsert(1, "alice2", "Alice2")
    u2 = await users_repo.get(1)
    assert u2.is_blocked is False
    assert u2.username == "alice2"


async def test_subscribe_is_idempotent(users_repo, tournaments_repo, subscriptions_repo):
    await users_repo.upsert(1, None, None)
    tid = await tournaments_repo.create("T", "")
    await subscriptions_repo.subscribe(1, tid)
    await subscriptions_repo.subscribe(1, tid)  # no error, no duplicate
    assert await subscriptions_repo.is_subscribed(1, tid) is True
    assert await subscriptions_repo.list_user_tournament_ids(1) == [tid]


async def test_unsubscribe(users_repo, tournaments_repo, subscriptions_repo):
    await users_repo.upsert(1, None, None)
    tid = await tournaments_repo.create("T", "")
    await subscriptions_repo.subscribe(1, tid)
    await subscriptions_repo.unsubscribe(1, tid)
    assert await subscriptions_repo.is_subscribed(1, tid) is False
    await subscriptions_repo.unsubscribe(1, tid)  # idempotent


async def test_all_active_ids_excludes_blocked(users_repo):
    await users_repo.upsert(1, None, None)
    await users_repo.upsert(2, None, None)
    await users_repo.upsert(3, None, None)
    await users_repo.mark_blocked(2)
    assert await users_repo.all_active_ids() == [1, 3]


async def test_subscribed_active_ids(
    users_repo, tournaments_repo, subscriptions_repo
):
    for uid in (1, 2, 3):
        await users_repo.upsert(uid, None, None)
    t1 = await tournaments_repo.create("T1", "")
    t2 = await tournaments_repo.create("T2", "")

    await subscriptions_repo.subscribe(1, t1)
    await subscriptions_repo.subscribe(2, t1)
    await subscriptions_repo.subscribe(3, t2)

    assert await users_repo.subscribed_active_ids(t1) == [1, 2]
    assert await users_repo.subscribed_active_ids(t2) == [3]

    await users_repo.mark_blocked(1)
    assert await users_repo.subscribed_active_ids(t1) == [2]
