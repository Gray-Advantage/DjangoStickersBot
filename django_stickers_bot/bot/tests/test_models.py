__all__ = ()

from django.db import IntegrityError, transaction
from django.test import TestCase

from bot.models import Sticker, StickerSet, TelegramUser


class StickerModelTest(TestCase):
    def setUp(self) -> None:
        self.user = TelegramUser.objects.create(telegram_id=1)
        self.sticker_set = StickerSet.objects.create(
            name="test_set",
            user=self.user,
        )

    def create_sticker(self, suffix: str, text: str = "текст") -> Sticker:
        return Sticker.objects.create(
            file_id=f"file-{suffix}",
            file_unique_id=f"unique-{suffix}",
            text=text,
            sticker_set=self.sticker_set,
        )

    def test_search_vector_filled_on_save(self) -> None:
        sticker = self.create_sticker("1", "дедлайн сегодня")
        sticker.refresh_from_db()

        self.assertIsNotNone(sticker.text_search_vector)

    def test_file_id_is_unique(self) -> None:
        self.create_sticker("1")

        with transaction.atomic(), self.assertRaises(IntegrityError):
            Sticker.objects.create(
                file_id="file-1",
                file_unique_id="unique-2",
                text="текст",
                sticker_set=self.sticker_set,
            )

    def test_deleting_set_deletes_its_stickers(self) -> None:
        self.create_sticker("1")

        self.sticker_set.delete()

        self.assertEqual(Sticker.objects.count(), 0)

    def test_str_returns_text(self) -> None:
        sticker = self.create_sticker("1", "текст стикера")

        self.assertEqual(str(sticker), "текст стикера")


class TelegramUserModelTest(TestCase):
    def test_defaults(self) -> None:
        user = TelegramUser.objects.create(telegram_id=42)

        self.assertFalse(user.is_admin)
        self.assertEqual(user.state, TelegramUser.UserStates.IDLE)
        self.assertEqual(user.context_data, "")
