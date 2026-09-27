__all__ = ()

from typing import cast

from aiogram.types import Message
from django.test import TestCase

from bot.bot.filters import Admin
from bot.models import TelegramUser


class FakeFromUser:
    def __init__(self, telegram_id: int) -> None:
        self.id = telegram_id


class FakeEvent:
    def __init__(self, telegram_id: int) -> None:
        self.from_user = FakeFromUser(telegram_id)


class AdminFilterTest(TestCase):
    async def test_admin_passes_and_gets_user(self) -> None:
        await TelegramUser.objects.acreate(telegram_id=11, is_admin=True)

        result = await Admin()(cast(Message, FakeEvent(11)))

        self.assertIsInstance(result, dict)
        user = cast(dict[str, TelegramUser], result)["user"]
        self.assertEqual(user.telegram_id, 11)

    async def test_ordinary_user_is_rejected(self) -> None:
        await TelegramUser.objects.acreate(telegram_id=22)

        self.assertFalse(await Admin()(cast(Message, FakeEvent(22))))

    async def test_unknown_user_is_rejected(self) -> None:
        self.assertFalse(await Admin()(cast(Message, FakeEvent(33))))
        self.assertTrue(
            await TelegramUser.objects.filter(telegram_id=33).aexists(),
        )
