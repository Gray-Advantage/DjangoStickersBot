__all__ = ()

import os
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from bot.models import TelegramUser


class InitAdminsCommandTest(TestCase):
    def call_with_admins(self, admin_ids: str) -> None:
        with mock.patch.dict(os.environ, {"BOT_ADMIN_USER_IDS": admin_ids}):
            call_command("init_admins")

    def test_creates_admins(self) -> None:
        self.call_with_admins("11,22")

        self.assertEqual(TelegramUser.objects.filter(is_admin=True).count(), 2)

    def test_promotes_existing_user(self) -> None:
        TelegramUser.objects.create(telegram_id=11)

        self.call_with_admins("11")

        user = TelegramUser.objects.get(telegram_id=11)
        self.assertTrue(user.is_admin)
        self.assertEqual(TelegramUser.objects.count(), 1)
