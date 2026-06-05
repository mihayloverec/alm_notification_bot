from __future__ import annotations


async def test_create_and_list_preserves_order(menu_buttons_repo):
    b1 = await menu_buttons_repo.create("A", "https://a")
    b2 = await menu_buttons_repo.create("B", "https://b")
    b3 = await menu_buttons_repo.create("C", "https://c")
    items = await menu_buttons_repo.list_all()
    assert [b.id for b in items] == [b1, b2, b3]
    assert [b.text for b in items] == ["A", "B", "C"]


async def test_update_text_and_url(menu_buttons_repo):
    bid = await menu_buttons_repo.create("Old", "https://old")
    await menu_buttons_repo.update_text(bid, "New")
    await menu_buttons_repo.update_url(bid, "https://new")
    b = await menu_buttons_repo.get(bid)
    assert b.text == "New"
    assert b.url == "https://new"


async def test_delete(menu_buttons_repo):
    bid = await menu_buttons_repo.create("X", "https://x")
    await menu_buttons_repo.delete(bid)
    assert await menu_buttons_repo.get(bid) is None
    assert await menu_buttons_repo.list_all() == []


async def test_move_up_swaps_with_previous(menu_buttons_repo):
    b1 = await menu_buttons_repo.create("A", "https://a")
    b2 = await menu_buttons_repo.create("B", "https://b")
    b3 = await menu_buttons_repo.create("C", "https://c")

    await menu_buttons_repo.move_up(b3)  # C ↑ → A, C, B
    items = await menu_buttons_repo.list_all()
    assert [b.id for b in items] == [b1, b3, b2]


async def test_move_down_swaps_with_next(menu_buttons_repo):
    b1 = await menu_buttons_repo.create("A", "https://a")
    b2 = await menu_buttons_repo.create("B", "https://b")
    b3 = await menu_buttons_repo.create("C", "https://c")

    await menu_buttons_repo.move_down(b1)  # A ↓ → B, A, C
    items = await menu_buttons_repo.list_all()
    assert [b.id for b in items] == [b2, b1, b3]


async def test_move_up_at_top_is_noop(menu_buttons_repo):
    b1 = await menu_buttons_repo.create("A", "https://a")
    b2 = await menu_buttons_repo.create("B", "https://b")
    await menu_buttons_repo.move_up(b1)
    items = await menu_buttons_repo.list_all()
    assert [b.id for b in items] == [b1, b2]


async def test_move_down_at_bottom_is_noop(menu_buttons_repo):
    b1 = await menu_buttons_repo.create("A", "https://a")
    b2 = await menu_buttons_repo.create("B", "https://b")
    await menu_buttons_repo.move_down(b2)
    items = await menu_buttons_repo.list_all()
    assert [b.id for b in items] == [b1, b2]
