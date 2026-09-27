__all__ = ()

from typing import ClassVar

from django.test import TestCase

from bot.models import Sticker, StickerSet, TelegramUser


class StickerSearchTest(TestCase):
    texts: ClassVar[dict[str, str]]

    @classmethod
    def setUpTestData(cls) -> None:
        user = TelegramUser.objects.create(telegram_id=1)
        sticker_set = StickerSet.objects.create(name="test_set", user=user)

        cls.texts = {
            "deadline": "Дедлайн сегодня, работу принимаю до вечера",
            "review": "Отправил проект на ревью, жду проверки",
            "empty": "<Пусто>",
        }
        for num, text in enumerate(cls.texts.values(), 1):
            Sticker.objects.create(
                file_id=f"file-{num}",
                file_unique_id=f"unique-{num}",
                text=text,
                sticker_set=sticker_set,
            )

    def test_finds_by_word_from_sticker(self) -> None:
        found = Sticker.objects.search("дедлайн")

        self.assertEqual([s.text for s in found], [self.texts["deadline"]])

    def test_finds_by_different_word_form(self) -> None:
        found = Sticker.objects.search("проверка")

        self.assertEqual([s.text for s in found], [self.texts["review"]])

    def test_finds_with_typo(self) -> None:
        found = Sticker.objects.search("дедлан")

        self.assertEqual([s.text for s in found], [self.texts["deadline"]])

    def test_unrelated_query_finds_nothing(self) -> None:
        self.assertEqual(len(Sticker.objects.search("велосипед")), 0)

    def test_more_relevant_sticker_goes_first(self) -> None:
        found = list(Sticker.objects.search("дедлайн работу"))

        self.assertGreater(len(found), 0)
        self.assertEqual(found[0].text, self.texts["deadline"])
