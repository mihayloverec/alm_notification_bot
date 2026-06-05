from __future__ import annotations

from bot.repositories import INQUIRY_DK, INQUIRY_SK


async def test_add_remove_and_list(users_repo, inquiry_recipients_repo):
    for uid in (10, 20, 30):
        await users_repo.upsert(uid, f"u{uid}", f"User {uid}")

    assert await inquiry_recipients_repo.has_any(INQUIRY_SK) is False
    assert await inquiry_recipients_repo.list_users(INQUIRY_SK) == []

    await inquiry_recipients_repo.add(INQUIRY_SK, 10)
    await inquiry_recipients_repo.add(INQUIRY_SK, 20)

    assert await inquiry_recipients_repo.has_any(INQUIRY_SK) is True
    assert await inquiry_recipients_repo.is_recipient(INQUIRY_SK, 10) is True
    assert await inquiry_recipients_repo.is_recipient(INQUIRY_SK, 30) is False

    users = await inquiry_recipients_repo.list_users(INQUIRY_SK)
    assert [u.user_id for u in users] == [10, 20]

    # типы изолированы
    assert await inquiry_recipients_repo.has_any(INQUIRY_DK) is False

    # idempotent add
    await inquiry_recipients_repo.add(INQUIRY_SK, 10)
    users2 = await inquiry_recipients_repo.list_users(INQUIRY_SK)
    assert [u.user_id for u in users2] == [10, 20]

    await inquiry_recipients_repo.remove(INQUIRY_SK, 10)
    assert await inquiry_recipients_repo.is_recipient(INQUIRY_SK, 10) is False

    # idempotent remove
    await inquiry_recipients_repo.remove(INQUIRY_SK, 10)


async def test_active_recipient_ids_excludes_banned_and_blocked(
    users_repo, inquiry_recipients_repo
):
    for uid in (1, 2, 3, 4):
        await users_repo.upsert(uid, None, None)
    for uid in (1, 2, 3, 4):
        await inquiry_recipients_repo.add(INQUIRY_SK, uid)

    await users_repo.mark_blocked(2)
    await users_repo.set_banned(3, True)

    ids = await inquiry_recipients_repo.list_active_recipient_ids(INQUIRY_SK)
    assert ids == [1, 4]

    # list_users возвращает всех (для админки), без фильтра
    all_users = await inquiry_recipients_repo.list_users(INQUIRY_SK)
    assert {u.user_id for u in all_users} == {1, 2, 3, 4}


async def test_recipient_cascade_on_user_delete(users_repo, inquiry_recipients_repo, conn):
    await users_repo.upsert(42, "x", "X")
    await inquiry_recipients_repo.add(INQUIRY_DK, 42)
    assert await inquiry_recipients_repo.is_recipient(INQUIRY_DK, 42) is True

    await conn.execute("DELETE FROM users WHERE user_id = 42")
    await conn.commit()

    assert await inquiry_recipients_repo.is_recipient(INQUIRY_DK, 42) is False
