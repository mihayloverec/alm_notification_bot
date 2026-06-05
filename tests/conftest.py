from __future__ import annotations

import pytest_asyncio

from bot import db
from bot.repositories import (
    InquiryRecipientsRepo,
    MenuButtonsRepo,
    OrganizersRepo,
    SubscriptionsRepo,
    TournamentsRepo,
    UsersRepo,
)


@pytest_asyncio.fixture
async def conn():
    c = await db.connect(":memory:")
    try:
        yield c
    finally:
        await c.close()


@pytest_asyncio.fixture
async def users_repo(conn):
    return UsersRepo(conn)


@pytest_asyncio.fixture
async def tournaments_repo(conn):
    return TournamentsRepo(conn)


@pytest_asyncio.fixture
async def subscriptions_repo(conn):
    return SubscriptionsRepo(conn)


@pytest_asyncio.fixture
async def inquiry_recipients_repo(conn):
    return InquiryRecipientsRepo(conn)


@pytest_asyncio.fixture
async def organizers_repo(conn):
    return OrganizersRepo(conn)


@pytest_asyncio.fixture
async def menu_buttons_repo(conn):
    return MenuButtonsRepo(conn)
