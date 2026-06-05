from __future__ import annotations


async def test_add_remove_and_idempotent(users_repo, organizers_repo):
    for uid in (1, 2, 3):
        await users_repo.upsert(uid, f"u{uid}", f"User {uid}")

    assert await organizers_repo.is_organizer(1) is False
    await organizers_repo.add(1)
    await organizers_repo.add(2)
    await organizers_repo.add(1)  # idempotent

    assert await organizers_repo.is_organizer(1) is True
    assert await organizers_repo.is_organizer(2) is True
    assert await organizers_repo.is_organizer(3) is False

    users = await organizers_repo.list_users()
    assert {u.user_id for u in users} == {1, 2}

    await organizers_repo.remove(1)
    assert await organizers_repo.is_organizer(1) is False
    await organizers_repo.remove(1)  # idempotent


async def test_cascade_on_user_delete(users_repo, organizers_repo, conn):
    await users_repo.upsert(42, "x", "X")
    await organizers_repo.add(42)
    assert await organizers_repo.is_organizer(42) is True

    await conn.execute("DELETE FROM users WHERE user_id = 42")
    await conn.commit()

    assert await organizers_repo.is_organizer(42) is False
